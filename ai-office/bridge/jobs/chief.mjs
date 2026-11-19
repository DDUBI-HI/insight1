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
        '목록에 없는 일은 만들지 않는다. 할 수 있는 첫 단계가 있으면 반드시 그 작업을 고른다. 정말 시작할 수 없을 때만(예: 파일 경로가 꼭 필요한 일) 작업을 고르지 말고 무엇이 필요한지 reply 에 구체적으로 묻는다.',
        '최대 3개까지 고른다. 도구는 쓰지 않는다. 대답은 아래 JSON 하나만 출력한다.',
        ['## 자주 하는 일 — 이렇게 나눈다',
          '- 카드뉴스 만들기·인스타그램 올리기: 주제가 있으면 cardnews.draft {topic}, 주제가 없으면 trend.research {autoDraft: true}(트렌드 조사 → 1번 주제로 초안까지 이어짐).',
          '  사진 선정·렌더·인스타그램 게시는 사용자가 승인함에서 초안과 게시를 승인하면 저절로 이어진다. 따로 고르지 말고, reply 에 "초안이 승인함에 올라오면 승인해 주세요"라고 알린다.',
          '- 트렌드·주제 찾기: trend.research {focus}',
          '- 교육 문의 분석: inquiry.analyze {title, body} (글이 요청에 있어야 함). 인사쟁이 대기 건 처리: 고르지 않는다(n8n·예약이 맡음).',
          '- 강사 프로필 정리·강사풀 PPT 추가: instructor.deck_add {file} 또는 instructor.intake {file} (파일 경로 필요). 강사풀 점검: instructor.verify',
          '- 고객사 제안서 범용화: proposal.generic {file} (파일 경로 필요)',
          '- 오늘 한 일 정리: chief.briefing 은 고르지 않는다(사용자가 직접 누름).'].join('\n'),
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
      const reply = String(out.reply || '').slice(0, 600);
      const summary = [`비서실장: ${reply || '(답 없음)'}`, ...notes].filter(Boolean).join(' / ');
      // 아무 일도 나누지 못했으면 질문을 승인함에 올려 사용자가 답할 수 있게 한다(작업 현황 한 줄로 묻히지 않게)
      if (!next.length && !approvals.length) {
        approvals.push({
          kind: 'chief.reply', worker: 'chief', title: '비서실장 질문 — 답장을 기다립니다',
          detail: `${reply || '요청을 어느 팀 일로 나눌지 정하지 못했습니다.'}${notes.length ? `\n\n참고: ${notes.join(' / ')}` : ''}\n\n아래 칸에 보충할 내용을 적고 '답장 보내기'를 누르면 다시 나눠서 시작합니다.`,
          data: { text: ctx.job.params.text },
        });
      }
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

