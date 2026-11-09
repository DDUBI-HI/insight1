// TEAM 3 · 콘텐츠마케팅팀
// 카드뉴스는 insight1 저장소의 /cardnews 에이전트를 복사본(설정 agents.cardnews)에서 두 번에 나눠 돌린다:
//   ① 초안(문구·인스타 글, 검증만) → 승인함  ② 승인 후 같은 세션을 이어서(--resume) 사진·렌더·압축
// 인스타그램 게시는 이 서버가 직접 하지 않는다(미연동). 승인하면 n8n 흐름이 설정된 경우에만 넘긴다.
import fs from 'node:fs';
import path from 'node:path';
import { asData, cleanInt, cleanText, copyNoOverwrite, extractJson, InputError, today, writeNoOverwrite } from '../util.mjs';
import { cardnewsState, COMMON_RULES, lineValue, requireAgent } from './common.mjs';

const SLUG_RE = /^\d{4}-\d{2}-[a-z0-9-]{3,60}$/;
const DRAFT_ALLOW = [
  'Read', 'Glob', 'Grep', 'Skill', 'TodoWrite', 'WebSearch',
  'Write(cardnews/decks/**)', 'Edit(cardnews/decks/**)',
  'Bash(cd:*)', 'Bash(ls:*)', 'Bash(node scripts/build-deck.mjs:*)', 'Bash(node cardnews/scripts/build-deck.mjs:*)',
];
const DRAFT_DENY = ['Bash(git:*)', 'Bash(npm:*)', 'Bash(npx:*)', 'Bash(rm:*)', 'Bash(curl:*)'];
const RENDER_ALLOW = [
  'Read', 'Glob', 'Grep', 'Skill', 'TodoWrite', 'WebSearch',
  'Write(cardnews/**)', 'Edit(cardnews/**)', 'Bash(cd:*)', 'Bash(ls:*)', 'Bash(node:*)', 'Bash(git:*)',
];
const RENDER_DENY = ['Bash(git push --force:*)', 'Bash(git push -f:*)', 'Bash(git reset --hard:*)', 'Bash(npm:*)', 'Bash(npx:*)', 'Bash(rm:*)', 'Bash(curl:*)'];

function draftApproval(jobId, sessionId, slug, text) {
  return {
    kind: 'cardnews.approve', worker: 't3-editor', title: `카드뉴스 초안 확인 — ${slug}`,
    detail: `${text}\n\n승인하면 사진 선정 → GitHub Actions 렌더 → 압축까지 진행합니다(GitHub 에 cardnews/${slug} 브랜치를 올립니다).\n고칠 점이 있으면 "수정 요청"에 의견을 적어 주세요.`,
    data: { draftJobId: jobId, sessionId, slug },
  };
}

function draftSource(store, id) {
  const j = store?.jobs.get(id);
  if (!j || !['cardnews.draft', 'cardnews.revise'].includes(j.type) || j.status !== 'done' || !j.result?.sessionId) throw new InputError('끝난 카드뉴스 초안 작업 번호가 필요합니다');
  return j;
}

export const team3Jobs = [
  {
    type: 'trend.research',
    team: 'team3', worker: 't3-research', label: '최신 트렌드 조사', heavy: false,
    desc: 'AI·HRD·리더십 최신 트렌드를 웹에서 조사해 출처와 함께 정리하고, 카드뉴스 주제 3개를 고릅니다. "초안까지 이어서"를 켜면 1번 주제로 카드뉴스 초안을 바로 만듭니다.',
    fields: [
      { name: 'focus', label: '조사 범위', kind: 'text', max: 100, placeholder: 'AI·HRD·리더십' },
      { name: 'autoDraft', label: '1번 주제로 카드뉴스 초안까지 이어서', kind: 'checkbox' },
    ],
    validate: (p) => ({ focus: cleanText(p.focus, { max: 100, label: '조사 범위', multiline: false }) || 'AI·HRD·리더십', autoDraft: p.autoDraft === true || p.autoDraft === 'true' }),
    title: (p) => `트렌드 조사: ${p.focus}`,
    async run(ctx) {
      const p = ctx.job.params;
      const prompt = [
        `너는 인싸이트러닝 콘텐츠마케팅팀 리서처다. 기업 HR·교육 담당자에게 도움이 될 "${p.focus}" 최신 트렌드를 WebSearch 로 조사한다(최근 3개월 우선).`,
        '규칙: 실제로 찾은 내용만 쓴다. 트렌드마다 확인한 출처 URL 을 단다. 확인 못 한 수치·통계는 쓰지 않는다.',
        '결과는 JSON 하나만: ```json\n{"trends":[{"title":"","summary":"두 문장","source_url":""}],"topics":[{"topic":"카드뉴스 주제","angle":"관점","audience":"대상"}]}\n``` (trends 5개, topics 3개)',
        COMMON_RULES,
      ].join('\n\n');
      const r = await ctx.claude({ prompt, cwd: ctx.emptyDir(), allow: ['WebSearch', 'WebFetch'], deny: ['Bash', 'Write', 'Edit'], timeoutMin: ctx.cfg.limits.lightJobTimeoutMinutes });
      if (!r.ok) throw new Error(r.error);
      const x = extractJson(r.result);
      if (!x || !Array.isArray(x.trends)) throw new Error('조사 결과(JSON)를 읽지 못했습니다');
      const md = [
        `# ${p.focus} 트렌드 (${new Date().toLocaleDateString('ko-KR')})`, '',
        ...x.trends.map((t, i) => `${i + 1}. **${t.title}** — ${t.summary}${t.source_url ? `\n   출처: ${t.source_url}` : ''}`), '',
        '## 카드뉴스 주제 후보', ...(x.topics || []).map((t, i) => `${i + 1}. ${t.topic} — ${t.angle || ''} (${t.audience || ''})`),
      ].join('\n');
      const file = writeNoOverwrite(path.join(ctx.paths.trends, `${today()}_트렌드.md`), md);
      const next = [];
      const top = (x.topics || [])[0];
      if (p.autoDraft && top?.topic) next.push({ type: 'cardnews.draft', params: { topic: String(top.topic).slice(0, 100), audience: String(top.audience || '').slice(0, 60) } });
      return { summary: `트렌드 ${x.trends.length}건, 주제 ${x.topics?.length || 0}개${next.length ? ` → "${top.topic}" 초안 요청` : ''}`, outputs: [file], next, result: x };
    },
  },
  {
    type: 'cardnews.draft',
    team: 'team3', worker: 't3-editor', label: '카드뉴스 초안 만들기', heavy: false,
    desc: '/cardnews 에이전트로 카드 구성·문구·인스타그램 글 초안을 만들고(검증까지), 승인함에 올립니다. 렌더·업로드는 승인 뒤에 합니다.',
    fields: [
      { name: 'topic', label: '주제', kind: 'text', required: true, max: 100 },
      { name: 'cards', label: '장수(7~20, 기본 13)', kind: 'number' },
      { name: 'audience', label: '대상(선택)', kind: 'text', max: 60, placeholder: '기업 HR·교육 담당자' },
    ],
    validate: (p) => ({
      topic: cleanText(p.topic, { max: 100, required: true, label: '주제', multiline: false }),
      cards: cleanInt(p.cards, { min: 7, max: 20, def: 13, label: '장수' }),
      audience: cleanText(p.audience, { max: 60, label: '대상', multiline: false }),
    }),
    title: (p) => `카드뉴스 초안: ${p.topic}`,
    async run(ctx) {
      requireAgent(cardnewsState(ctx.cfg), ctx.cfg);
      const p = ctx.job.params;
      const prompt = [
        `카드뉴스 만들어줘. /cardnews 절차(.claude/skills/cardnews/SKILL.md)를 따른다.`,
        asData('request', `주제: ${p.topic}\n장수: ${p.cards}\n대상: ${p.audience || '기업 HR·교육 담당자'}`),
        '이번 실행은 SKILL.md 의 "2. 구성과 문구 초안"까지만 한다: deck.json 작성 → `node scripts/build-deck.mjs decks/<slug> --check` 통과 → 초안 표와 인스타그램 문구를 출력하고 멈춘다.',
        '사진 선정·생성·렌더·커밋·push 는 하지 않는다(사용자 승인 뒤 같은 대화를 이어서 한다).',
        COMMON_RULES,
        '맨 마지막 줄에 `SLUG: <slug>` 를 쓴다.',
      ].join('\n\n');
      const r = await ctx.claude({ prompt, cwd: ctx.cfg.demo ? ctx.emptyDir() : ctx.cfg.agents.cardnews, allow: DRAFT_ALLOW, deny: DRAFT_DENY, timeoutMin: 30 });
      if (!r.ok) throw new Error(r.error);
      const slug = lineValue(r.result, 'SLUG');
      if (!SLUG_RE.test(slug)) throw new Error('덱 이름(SLUG)을 받지 못했습니다');
      return { summary: `초안 완성: ${slug} — 승인함에서 확인하세요`, approvals: [draftApproval(ctx.job.id, r.sessionId, slug, r.result.replace(/^\s*SLUG:.*$/m, '').trim())], result: { sessionId: r.sessionId, slug } };
    },
  },
  {
    type: 'cardnews.revise',
    team: 'team3', worker: 't3-editor', label: '카드뉴스 초안 고치기', heavy: false, chiefCallable: false,
    desc: '승인함의 "수정 요청" 의견을 같은 대화에 이어서 반영합니다.',
    fields: [{ name: 'draftJobId', label: '초안 작업 번호', kind: 'text', required: true }, { name: 'note', label: '수정 의견', kind: 'textarea', required: true, max: 2000 }],
    validate: (p, cfg, store) => { draftSource(store, p.draftJobId); return { draftJobId: p.draftJobId, note: cleanText(p.note, { max: 2000, required: true, label: '수정 의견' }) }; },
    title: () => '카드뉴스 초안 고치기',
    async run(ctx) {
      requireAgent(cardnewsState(ctx.cfg), ctx.cfg);
      const src = draftSource(ctx.store, ctx.job.params.draftJobId);
      const prompt = ['사용자 수정 의견을 반영해 deck.json 을 고치고 --check 검증을 다시 통과시킨 뒤, 바뀐 초안 표와 인스타그램 문구를 다시 보여 주고 멈춘다. 렌더·커밋·push 는 하지 않는다.',
        asData('request', ctx.job.params.note), '맨 마지막 줄에 `SLUG: <slug>` 를 쓴다.'].join('\n\n');
      const r = await ctx.claude({ prompt, cwd: ctx.cfg.demo ? ctx.emptyDir() : ctx.cfg.agents.cardnews, resume: src.result.sessionId, allow: DRAFT_ALLOW, deny: DRAFT_DENY, timeoutMin: 30 });
      if (!r.ok) throw new Error(r.error);
      const slug = lineValue(r.result, 'SLUG') || src.result.slug;
      return { summary: `수정본 완성: ${slug}`, approvals: [draftApproval(ctx.job.id, r.sessionId || src.result.sessionId, slug, r.result.replace(/^\s*SLUG:.*$/m, '').trim())], result: { sessionId: r.sessionId || src.result.sessionId, slug } };
    },
  },
  {
    type: 'cardnews.render',
    team: 'team3', worker: 't3-editor', label: '카드뉴스 완성(사진·렌더·압축)', heavy: true, chiefCallable: false,
    desc: '승인된 초안을 이어서 사진 선정 → GitHub Actions 렌더 → 검수 → 압축까지 하고, 결과를 콘텐츠 폴더에 모읍니다.',
    fields: [{ name: 'draftJobId', label: '초안 작업 번호', kind: 'text', required: true }],
    validate: (p, cfg, store) => { draftSource(store, p.draftJobId); return { draftJobId: p.draftJobId }; },
    title: () => '카드뉴스 완성',
    async run(ctx) {
      requireAgent(cardnewsState(ctx.cfg), ctx.cfg);
      const src = draftSource(ctx.store, ctx.job.params.draftJobId);
      const slug = src.result.slug;
      const prompt = [
        '사용자가 초안을 승인했습니다. SKILL.md 의 3~7단계를 이어서 진행한다.',
        `- 4단계의 로컬 레이아웃 렌더는 건너뛰고 CI 렌더에 맡긴다.`,
        `- 5단계: 지금 브랜치에서 \`cardnews/${slug}\` 브랜치를 새로 만들어(git switch -c) 커밋하고 그 브랜치로 push 한다. PR 은 만들지 않는다. 강제 push 금지.`,
        '- 렌더 커밋을 기다릴 때는 git ls-remote 로 1분 간격 확인, 최대 20분. 그 뒤 pull.',
        '- 6단계 시각 검수, 7단계 압축(node scripts/pack-deck.mjs)까지 한다.',
        COMMON_RULES.replace('- git commit·push 를 하지 않는다(이 작업에서 따로 허락한 경우 제외).\n', ''),
        `맨 마지막 줄에 \`ZIP: cardnews/dist/${slug}.zip\` 처럼 압축 파일 경로를 쓴다.`,
      ].join('\n');
      const r = await ctx.claude({ prompt, cwd: ctx.cfg.demo ? ctx.emptyDir() : ctx.cfg.agents.cardnews, resume: src.result.sessionId, allow: RENDER_ALLOW, deny: RENDER_DENY, timeoutMin: 60 });
      const dest = path.join(ctx.paths.cardnews, slug);
      fs.mkdirSync(dest, { recursive: true });
      const files = [];
      if (ctx.cfg.demo) files.push(writeNoOverwrite(path.join(dest, `${slug}(데모).txt`), '데모 모드 결과입니다. 실제 카드 이미지는 만들지 않았습니다.\n'));
      else {
        const repo = ctx.cfg.agents.cardnews;
        const zip = path.join(repo, 'cardnews', 'dist', `${slug}.zip`);
        if (fs.existsSync(zip)) files.push(copyNoOverwrite(zip, path.join(dest, `${slug}.zip`)));
        for (const f of ['caption.txt', 'CREDITS.md', 'out/overview.png']) {
          const s = path.join(repo, 'cardnews', 'decks', slug, f);
          if (fs.existsSync(s)) files.push(copyNoOverwrite(s, path.join(dest, path.basename(f))));
        }
      }
      if (!r.ok && !files.length) throw new Error(r.error);
      const capFile = files.find((f) => f.endsWith('caption.txt'));
      const caption = capFile ? fs.readFileSync(capFile, 'utf8') : '(인스타그램 문구 파일 없음)';
      return {
        summary: files.length ? `완성 파일 ${files.length}개를 콘텐츠 폴더에 모았습니다` : '결과 파일을 찾지 못했습니다',
        outputs: [dest, ...files],
        approvals: [{
          kind: 'instagram.publish', worker: 't3-editor', title: `인스타그램 게시 승인 — ${slug}`, files,
          detail: `${caption}\n\n${r.ok ? '' : `주의: 작업이 정상 종료되지 않았습니다 — ${r.error}\n`}승인해도 인스타그램 계정 연동 전에는 자동 게시하지 않습니다. 압축 파일로 직접 올려 주세요.`,
          data: { slug, dest },
        }],
        result: { slug },
      };
    },
  },
];
