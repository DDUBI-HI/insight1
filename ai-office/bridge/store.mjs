// 작업·승인함 저장소. 작업마다 <dataDir>/jobs/<id>/job.json, 승인은 <dataDir>/jobs/approvals.json.
// 서버가 다시 켜지면 '실행 중'이던 작업은 '중단됨'으로 바꾼다(실행 중인 Claude 는 서버와 함께 끝났기 때문).
import fs from 'node:fs';
import path from 'node:path';
import { ID_RE, newId, readJsonSafe, writeJsonAtomic } from './util.mjs';

const MAX_LOG = 400;

export class Store {
  constructor(paths) {
    this.paths = paths;
    this.jobs = new Map();
    this.approvals = new Map();
    this.events = []; // { at, worker, k, a } — 3D 화면 활동 로그
    this.listeners = new Set();
    this.load();
  }

  load() {
    fs.mkdirSync(this.paths.jobs, { recursive: true });
    for (const name of fs.readdirSync(this.paths.jobs)) {
      if (!ID_RE.test(name)) continue;
      const j = readJsonSafe(path.join(this.paths.jobs, name, 'job.json'));
      if (!j) continue;
      if (j.status === 'running' || j.status === 'queued') {
        j.status = j.status === 'running' ? 'failed' : 'canceled';
        j.error = j.error || '서버가 다시 시작되어 중단되었습니다. 필요하면 다시 요청하세요.';
        j.finishedAt = j.finishedAt || new Date().toISOString();
        this.writeJob(j);
      }
      this.jobs.set(j.id, j);
    }
    const ap = readJsonSafe(path.join(this.paths.jobs, 'approvals.json'), []);
    for (const a of Array.isArray(ap) ? ap : []) this.approvals.set(a.id, a);
  }

  on(fn) { this.listeners.add(fn); return () => this.listeners.delete(fn); }
  emit(type, data) { for (const fn of this.listeners) { try { fn(type, data); } catch { /* 듣는 쪽 오류 무시 */ } } }

  jobDir(id) { return path.join(this.paths.jobs, id); }
  writeJob(j) { writeJsonAtomic(path.join(this.jobDir(j.id), 'job.json'), j); }

  createJob({ type, team, worker, title, params, source = 'panel', heavy = false, parentId = null }) {
    const j = {
      id: newId('J'), type, team, worker, title, params, source, heavy, parentId,
      status: 'queued', createdAt: new Date().toISOString(), startedAt: null, finishedAt: null,
      summary: '', error: '', outputs: [], sessionId: null, log: [], result: null,
    };
    fs.mkdirSync(this.jobDir(j.id), { recursive: true });
    this.writeJob(j);
    this.jobs.set(j.id, j);
    this.event(worker, 'text', `작업 접수: ${title}`);
    this.emit('job', j);
    return j;
  }

  updateJob(id, patch) {
    const j = this.jobs.get(id);
    if (!j) return null;
    Object.assign(j, patch);
    this.writeJob(j);
    this.emit('job', j);
    return j;
  }

  logJob(id, line) {
    const j = this.jobs.get(id);
    if (!j) return;
    j.log.push({ at: new Date().toISOString(), line: String(line).slice(0, 500) });
    if (j.log.length > MAX_LOG) j.log.splice(0, j.log.length - MAX_LOG);
    try { fs.appendFileSync(path.join(this.jobDir(id), 'log.txt'), `[${new Date().toISOString()}] ${line}\n`, 'utf8'); } catch { /* 로그 실패는 무시 */ }
  }

  event(worker, k, a) {
    this.events.push({ at: new Date().toISOString(), worker, k, a: String(a ?? '').slice(0, 80) });
    if (this.events.length > 300) this.events.splice(0, this.events.length - 300);
  }

  listJobs(limit = 100) {
    return [...this.jobs.values()].sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1)).slice(0, limit);
  }

  saveApprovals() { writeJsonAtomic(path.join(this.paths.jobs, 'approvals.json'), [...this.approvals.values()]); }

  addApproval({ kind, jobId, worker, title, detail = '', data = {}, files = [] }) {
    const a = {
      id: newId('A'), kind, jobId, worker, title, detail: String(detail).slice(0, 20000), data, files,
      status: 'pending', createdAt: new Date().toISOString(), decidedAt: null, note: '', outcome: '',
    };
    this.approvals.set(a.id, a);
    this.saveApprovals();
    this.event(worker, 'text', `승인 요청: ${title}`);
    this.emit('approval', a);
    return a;
  }

  decideApproval(id, patch) {
    const a = this.approvals.get(id);
    if (!a) return null;
    Object.assign(a, patch, { decidedAt: new Date().toISOString() });
    this.saveApprovals();
    this.emit('approval', a);
    return a;
  }

  pendingApprovals() {
    return [...this.approvals.values()].filter((a) => a.status === 'pending').sort((a, b) => (a.createdAt < b.createdAt ? -1 : 1));
  }
}
