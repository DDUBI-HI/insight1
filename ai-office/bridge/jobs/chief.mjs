// AI 비서실장 — 자연어 요청을 팀 작업으로 나누고, 하루 업무를 정리한다.
import path from 'node:path';
import { cleanText, extractJson, today, writeNoOverwrite, asData } from '../util.mjs';
import { COMMON_RULES, TEAMS, WORKERS } from './common.mjs';

export const chiefJobs = [
  {
    type: 'chief.request',
    team: 'chief', worker: 'chief', label: '비서실장에게 요청', heavy: false,
    desc: '하고 싶은 일을 평소 말투로 적으면 비서실장이 맞는 팀 작업으로 나눕니다. 무거운 작업은 승인함에 올립니다.',
    fields: [{ name: 'text', label: '요청 내용', kind: 'textarea', required: true, max: 3000, placeholder: '예) 이번 주 카드뉴스 주제 좀 찾아줘' }],
    validate: (p) => ({ text: cleanText(p.text, { max: 3000, required: true, label: '요청 내용' }) }),
    title: (p) => `요청 정리: ${p.text.slice(0, 30)}`,
    async run(ctx) {
      const list = ctx.registry.list().filter((d) => d.chiefCallable !== false && !d.type.startsWith('chief.'));
      const catalog = list.map((d) => ({
        type: d.type, team: TEAMS[d.team], worker: WORKERS[d.worker].name, what: d.desc, heavy: !!d.heavy,
        params: (d.fields || []).map((f) => `${f.name}${f.required ? '(필수)' : ''}: ${f.label}${f.kind === 'file' ? ' — C:\\ 로 시작하는 파일 전체 경로' : ''}`),
      }));
      const prompt = [
        '너는 인싸이트러닝 AI 사무실의 비서실장이다. 사용자의 요청을 읽고, 아래 작업 목록 중에서 실행할 작업을 고른다.',
        '목록에 없는 일은 만들지 않는다. 필요한 값(파일 경로 등)이 요청에 없으면 작업을 고르지 말고 무엇이 필요한지 reply 에 쓴다.',
        '최대 3개까지 고른다. 도구는 쓰지 않는다. 대답은 아래 JSON 하나만 출력한다.',
        '```json\n{"reply":"사용자에게 할 말(한국어, 2문장 이내)","actions":[{"type":"작업 type","params":{},"reason":"고른 이유"}]}\n```',
        COMMON_RULES,
        '## 작업 목록', JSON.stringify(catalog, null, 1),
        '## 사용자 요청', asData('request', ctx.job.params.text),
      ].join('\n\n');
      const r = await ctx.claude({ prompt, cwd: ctx.emptyDir(), allow: [], deny: ['Bash', 'Write', 'Edit', 'WebFetch', 'WebSearch'], timeoutMin: 10 });
      if (!r.ok) throw new Error(r.error);
      const out = extractJson(r.result);
      if (!out) throw new Error('비서실장 답을 읽지 못했습니다: ' + r.result.slice(0, 200));
      const notes = [];
      const next = []; const approvals = [];
      for (const a of (Array.isArray(out.actions) ? out.actions : []).slice(0, 3)) {
        const def = ctx.registry.get(a?.type);
        if (!def || def.type.startsWith('chief.')) { notes.push(`모르는 작업은 건너뜀: ${a?.type}`); continue; }
        let params;
        try { params = def.validate(a.params || {}, ctx.cfg, ctx.store); } catch (e) { notes.push(`${def.label}: ${e.message}`); continue; }
        if (def.heavy) {
          approvals.push({
            kind: 'chief.dispatch', worker: def.worker,
            title: `비서실장 제안 — ${def.label} 실행`,
            detail: `${a.reason || ''}\n\n이 작업은 오래 걸리고 Claude 사용량이 많습니다. 승인하면 바로 시작합니다.\n\n${JSON.stringify(params, null, 2)}`,
            data: { type: def.type, params },
          });
        } else next.push({ type: def.type, params });
      }
      const summary = [String(out.reply || '').slice(0, 300), ...notes].filter(Boolean).join(' / ');
      return { summary, next, approvals, result: out };
    },
  },
  {
    type: 'chief.briefing',
    team: 'chief', worker: 'chief', label: '오늘 업무 브리핑', heavy: false,
    desc: '최근 24시간 작업 결과와 승인 대기 목록을 한 장으로 정리합니다(Claude 사용량 없음).',
    fields: [],
    validate: () => ({}),
    title: () => '오늘 업무 브리핑',
    async run(ctx) {
      const since = Date.now() - 24 * 3600 * 1000;
      const jobs = ctx.store.listJobs(500).filter((j) => Date.parse(j.createdAt) >= since && j.id !== ctx.job.id);
      const pend = ctx.store.pendingApprovals();
      const by = (s) => jobs.filter((j) => j.status === s);
      const line = (j) => `- [${TEAMS[j.team]}] ${j.title} — ${j.summary || j.error || j.status}`;
      const md = [
        `# 비서실장 브리핑 (${new Date().toLocaleString('ko-KR')})`, '',
        `- 최근 24시간 작업 ${jobs.length}건: 완료 ${by('done').length}, 실패 ${by('failed').length}, 진행·대기 ${by('running').length + by('queued').length}`,
        `- 승인 대기 ${pend.length}건`, '',
        '## 승인 대기', ...(pend.length ? pend.map((a) => `- ${a.title} (${new Date(a.createdAt).toLocaleString('ko-KR')})`) : ['- 없음']), '',
        '## 완료', ...(by('done').length ? by('done').map(line) : ['- 없음']), '',
        '## 실패 — 확인 필요', ...(by('failed').length ? by('failed').map(line) : ['- 없음']), '',
      ].join('\n');
      const file = writeNoOverwrite(path.join(ctx.paths.reports, `비서실장_브리핑_${today()}.md`), md);
      return { summary: `작업 ${jobs.length}건, 승인 대기 ${pend.length}건을 정리했습니다`, outputs: [file] };
    },
  },
];

