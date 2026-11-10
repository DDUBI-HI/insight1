// 작업 줄 세우기와 실행. 한 번에 한 작업만 돈다(PowerPoint 렌더는 동시에 둘 못 돌리고, Pro 사용량도 아낀다).
import fs from 'node:fs';
import path from 'node:path';
import { runClaude, runPython, venvPython } from './claude.mjs';
import { decide } from './jobs/index.mjs';
import { loadN8nSecret } from './config.mjs';
import { InputError, readJsonSafe, writeJsonAtomic } from './util.mjs';

const DAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];

export class Runner {
  constructor({ cfg, paths, store, registry }) {
    Object.assign(this, { cfg, paths, store, registry });
    this.current = null; // { jobId, act, kill }
    this.timer = null;
  }

  enqueue(type, params = {}, { source = 'panel', parentId = null } = {}) {
    const def = this.registry.get(type);
    if (!def) throw new InputError(`허용되지 않은 작업입니다: ${type}`);
    if (!['panel', 'n8n', 'chain', 'approval', 'schedule', 'chief', 'test'].includes(source)) source = 'panel';
    const clean = def.validate(params && typeof params === 'object' ? params : {}, this.cfg, this.store);
    const job = this.store.createJob({ type, team: def.team, worker: def.worker, title: def.title(clean), params: clean, source, heavy: !!def.heavy, parentId });
    setImmediate(() => this.kick());
    return job;
  }

  cancel(id) {
    const j = this.store.jobs.get(id);
    if (!j) return null;
    if (j.status === 'queued') return this.store.updateJob(id, { status: 'canceled', finishedAt: new Date().toISOString(), error: '사용자가 취소했습니다' });
    if (j.status === 'running' && this.current?.jobId === id) { this.current.canceled = true; this.current.kill?.(); return j; }
    return j;
  }

  queued() { return [...this.store.jobs.values()].filter((j) => j.status === 'queued').sort((a, b) => (a.createdAt < b.createdAt ? -1 : 1)); }

  async kick() {
    if (this.current) return;
    const job = this.queued()[0];
    if (!job) return;
    this.current = { jobId: job.id, act: null, kill: null, canceled: false };
    try { await this.run(job); } finally { this.current = null; setImmediate(() => this.kick()); }
  }

  ctxFor(job) {
    const { cfg, paths, store } = this;
    const dir = store.jobDir(job.id);
    let n = 0;
    const ctx = {
      cfg, paths, store, registry: this.registry, job, dir,
      log: (line) => store.logJob(job.id, line),
      act: (a) => { if (this.current) this.current.act = a; store.event(job.worker, a.k, a.a); },
      emptyDir: () => { const d = path.join(paths.run, job.id, 'empty'); fs.mkdirSync(d, { recursive: true }); return d; },
      python: (args, opts = {}) => {
        const slide = cfg.agents?.slideSvg;
        const py = slide && venvPython(slide);
        if (!py) throw new Error('slide-svg 복사본의 Python 가상환경(.venv)을 찾지 못했습니다');
        return runPython(py, args, { cwd: slide, ...opts });
      },
      claude: async (opts) => {
        n += 1;
        ctx.log(`Claude 실행 #${n} (폴더: ${opts.cwd})`);
        const r = await runClaude(cfg, {
          ...opts,
          mockTag: opts.mockTag || job.type,
          timeoutMin: opts.timeoutMin || cfg.limits.jobTimeoutMinutes,
          settingsFile: path.join(paths.run, job.id, `claude-${n}-settings.json`),
          onAct: (a) => ctx.act(a),
          onLog: (l) => ctx.log(l),
          onStart: (kill) => { if (this.current) this.current.kill = kill; },
        });
        if (r.sessionId) store.updateJob(job.id, { sessionId: r.sessionId });
        ctx.log(`Claude 끝 #${n}: ${r.ok ? '성공' : '실패 — ' + r.error}${r.denials?.length ? ` / 거부된 도구: ${r.denials.join(', ')}` : ''}`);
        if (this.current?.canceled) throw new Error('사용자가 취소했습니다');
        return r;
      },
    };
    return ctx;
  }

  async run(job) {
    const def = this.registry.get(job.type);
    this.store.updateJob(job.id, { status: 'running', startedAt: new Date().toISOString() });
    this.store.event(job.worker, 'text', `시작: ${job.title}`);
    const ctx = this.ctxFor(job);
    try {
      const res = (await def.run(ctx)) || {};
      const patch = { status: 'done', finishedAt: new Date().toISOString(), summary: String(res.summary || '완료').slice(0, 600), outputs: res.outputs || [] };
      if (res.result !== undefined) patch.result = { ...(res.result || {}), sessionId: res.result?.sessionId || this.store.jobs.get(job.id).sessionId || null };
      this.store.updateJob(job.id, patch);
      for (const a of res.approvals || []) this.store.addApproval({ ...a, jobId: job.id, worker: a.worker || job.worker });
      for (const nx of res.next || []) {
        try { this.enqueue(nx.type, nx.params, { source: 'chain', parentId: job.id }); }
        catch (e) { ctx.log(`이어지는 작업을 만들지 못함(${nx.type}): ${e.message}`); }
      }
      this.store.event(job.worker, 'text', `완료: ${patch.summary}`);
      this.notify('job.done', job.id);
    } catch (e) {
      const msg = String(e?.message || e).slice(0, 600);
      ctx.log(`실패: ${msg}`);
      this.store.updateJob(job.id, { status: this.current?.canceled ? 'canceled' : 'failed', finishedAt: new Date().toISOString(), error: msg });
      this.store.event(job.worker, 'text', `실패: ${msg.slice(0, 50)}`);
      this.notify('job.failed', job.id);
    }
  }

  async decideApproval(id, decision, note) {
    const a = this.store.approvals.get(id);
    if (!a) throw new InputError('승인 항목이 없습니다');
    if (a.status !== 'pending') throw new InputError('이미 처리한 항목입니다');
    if (!['approve', 'reject', 'revise'].includes(decision)) throw new InputError('결정 값이 올바르지 않습니다');
    const r = await decide(a, decision, note, { cfg: this.cfg, paths: this.paths, postN8n: (u, b) => this.postN8n(u, b) });
    const enq = [];
    for (const e of r.enqueue || []) {
      try { enq.push(this.enqueue(e.type, e.params, { source: 'approval', parentId: a.jobId }).id); }
      catch (err) { r.outcome += ` (작업을 만들지 못함: ${err.message})`; }
    }
    this.store.decideApproval(id, { status: decision === 'approve' ? 'approved' : decision === 'revise' ? 'revised' : 'rejected', note: note || '', outcome: r.outcome, enqueued: enq });
    this.store.event(a.worker, 'text', `${decision === 'approve' ? '승인됨' : '반려/수정'}: ${a.title}`);
    return this.store.approvals.get(id);
  }

  // ---- n8n 알림(설정했을 때만) ----
  async postN8n(url, body) {
    try {
      const u = new URL(url);
      if (!['http:', 'https:'].includes(u.protocol)) return { ok: false, error: '주소 형식 오류' };
      const headers = { 'content-type': 'application/json' };
      headers['x-office-secret'] = loadN8nSecret(this.cfg);
      const res = await fetch(u, { method: 'POST', headers, body: JSON.stringify(body), signal: AbortSignal.timeout(15000) });
      return res.ok ? { ok: true } : { ok: false, error: `HTTP ${res.status}` };
    } catch (e) { return { ok: false, error: e.message }; }
  }

  notify(event, jobId) {
    const url = this.cfg.n8n?.webhooks?.events;
    if (!url) return;
    const j = this.store.jobs.get(jobId);
    const pending = this.store.pendingApprovals().filter((a) => a.jobId === jobId).map((a) => a.title);
    this.postN8n(url, { event, id: j.id, type: j.type, team: j.team, title: j.title, status: j.status, summary: j.summary, error: j.error, approvals: pending })
      .then((r) => { if (!r.ok) this.store.logJob(jobId, `n8n 알림 실패: ${r.error}`); });
  }

  // ---- 내장 예약(설정 schedule, 기본 꺼짐). n8n 예약 흐름을 쓰면 이것은 비워 둔다 ----
  startScheduler() {
    const stateFile = path.join(this.paths.run, 'schedule-state.json');
    const state = readJsonSafe(stateFile, {});
    const tick = () => {
      const now = new Date();
      const day = DAYS[now.getDay()];
      const hm = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      const date = now.toISOString().slice(0, 10);
      (this.cfg.schedule || []).forEach((s, i) => {
        if (!s || s.enabled === false || !s.type || s.time !== hm) return;
        if (Array.isArray(s.days) && s.days.length && !s.days.map((d) => String(d).toUpperCase()).includes(day)) return;
        const key = `${i}:${s.type}`;
        if (state[key] === `${date} ${hm}`) return;
        state[key] = `${date} ${hm}`;
        writeJsonAtomic(stateFile, state);
        try { this.enqueue(s.type, s.params || {}, { source: 'schedule' }); } catch (e) { this.store.event('chief', 'text', `예약 실패: ${e.message}`); }
      });
    };
    this.timer = setInterval(tick, 20 * 1000);
    this.timer.unref?.();
  }
}
