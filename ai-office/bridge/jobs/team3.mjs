// TEAM 3 · 콘텐츠마케팅팀
// 카드뉴스는 insight1 저장소의 /cardnews 에이전트를 복사본(설정 agents.cardnews)에서 두 번에 나눠 돌린다:
//   ① 초안(문구·인스타 글, 검증만) → 승인함  ② 승인 후 같은 세션을 이어서(--resume) 사진·렌더·압축
// 인스타그램 게시는 이 서버가 직접 하지 않는다(미연동). 승인하면 n8n 흐름이 설정된 경우에만 넘긴다.
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { ROOT, loadN8nSecret } from '../config.mjs';
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

// git 을 정해진 인자로만 실행(셸 없음)
function git(cwd, args, timeoutMin = 5) {
  return new Promise((resolve) => {
    const c = spawn('git', args, { cwd, windowsHide: true, shell: false });
    let out = ''; let err = '';
    c.stdout.on('data', (d) => { out += d; }); c.stderr.on('data', (d) => { err += d; });
    const t = setTimeout(() => c.kill(), timeoutMin * 60000);
    c.on('error', (e) => { err += e.message; });
    c.on('close', (code) => { clearTimeout(t); resolve({ code, out: out.trim(), err: err.trim() }); });
  });
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

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
    type: 'instagram.publish',
    team: 'team3', worker: 't3-editor', label: '인스타그램 게시', heavy: false, chiefCallable: false,
    desc: '승인된 카드뉴스를 인스타그램 게시용 JPEG(4:5)로 바꿔 GitHub 공개 주소에 올리고, n8n 인스타그램 흐름으로 캐러셀 게시합니다. 승인함에서 "게시 승인"을 눌렀을 때만 시작합니다.',
    fields: [{ name: 'slug', label: '덱 이름', kind: 'text', required: true }],
    validate: (p) => { const slug = cleanText(p.slug, { max: 80, required: true, label: '덱 이름', multiline: false }); if (!SLUG_RE.test(slug)) throw new InputError('덱 이름 형식이 아닙니다'); return { slug }; },
    title: (p) => `인스타그램 게시: ${p.slug}`,
    async run(ctx) {
      const { slug } = ctx.job.params;
      const hook = ctx.cfg.n8n?.webhooks?.instagramPublish;
      if (ctx.cfg.demo) {
        await ctx.claude({ prompt: 'demo', cwd: ctx.emptyDir(), mockTag: 'cardnews.render', allow: [], timeoutMin: 5 });
        return { summary: '(데모) 인스타그램 게시를 흉내 냈습니다 — 실제로 올리지 않았습니다', result: { slug, permalink: null } };
      }
      if (!ctx.cfg.instagram?.enabled || !hook) throw new Error('인스타그램 미연동 — config.json 의 instagram.enabled 와 n8n.webhooks.instagramPublish 를 먼저 설정하세요');
      requireAgent(cardnewsState(ctx.cfg), ctx.cfg);
      const repo = ctx.cfg.agents.cardnews;
      const branch = `cardnews/${slug}`;
      const deckDir = path.join(repo, 'cardnews', 'decks', slug);
      const outDir = path.join(deckDir, 'out');
      const igDir = path.join(outDir, 'instagram');
      const step = async (label, args) => { ctx.log(`git ${args.join(' ')}`); ctx.act({ k: 'bash', a: label }); const r = await git(repo, args); if (r.code !== 0) throw new Error(`${label} 실패: ${(r.err || r.out).slice(-300)}`); return r; };
      await step('브랜치 이동', ['switch', branch]);
      await step('렌더 결과 받기', ['pull', '--ff-only', 'origin', branch]);
      if (!fs.existsSync(outDir)) throw new Error(`렌더된 카드가 없습니다: ${outDir}`);
      // 1) JPEG(4:5) 변환
      ctx.act({ k: 'bash', a: 'JPEG 변환' });
      const max = Number(ctx.cfg.instagram.maxImages) || 10;
      const conv = await ctx.python([path.join(ROOT, 'tools', 'instagram_images.py'), outDir, igDir, '--max', String(max), '--size', String(ctx.cfg.instagram.size || '1080x1350')]);
      let info = null; try { info = JSON.parse(conv.stdout); } catch { /* 아래 */ }
      if (!info?.ok) throw new Error(`JPEG 변환 실패: ${(info?.error || conv.stderr || conv.stdout).slice(-300)}`);
      // 2) 공개 주소에 올리기(같은 카드뉴스 브랜치, out/ 아래라 렌더 워크플로는 다시 돌지 않는다)
      await step('JPEG 올리기 준비', ['add', '--', path.relative(repo, igDir)]);
      const st = await git(repo, ['diff', '--cached', '--quiet']);
      if (st.code !== 0) await step('JPEG 커밋', ['commit', '-m', `cardnews: ${slug} instagram jpeg [skip ci]`]);
      await step('GitHub 에 올리기', ['push', 'origin', branch]);
      const remote = (await git(repo, ['remote', 'get-url', 'origin'])).out;
      const m = remote.match(/github\.com[/:]([^/]+)\/([^/.]+)(?:\.git)?$/);
      if (!m) throw new Error(`GitHub 저장소 주소를 알 수 없습니다: ${remote}`);
      const enc = (p) => p.split('/').map(encodeURIComponent).join('/');
      const urls = info.files.map((f) => `https://raw.githubusercontent.com/${m[1]}/${m[2]}/${enc(branch)}/${enc(path.relative(repo, f).split(path.sep).join('/'))}`);
      // 3) 공개 주소가 열리는지 확인(최대 3분)
      ctx.act({ k: 'fetch', a: 'raw.githubusercontent.com' });
      for (let i = 0; ; i++) {
        const ok = await Promise.all(urls.map((u) => fetch(u, { method: 'HEAD', signal: AbortSignal.timeout(10000) }).then((r) => r.ok).catch(() => false)));
        if (ok.every(Boolean)) break;
        if (i >= 18) throw new Error('GitHub 공개 주소에서 사진을 열 수 없습니다(저장소가 비공개인지 확인)');
        await sleep(10000);
      }
      // 4) 인스타그램 문구
      const capFile = path.join(deckDir, 'caption.txt');
      const caption = fs.existsSync(capFile) ? fs.readFileSync(capFile, 'utf8').trim() : '';
      if (!caption) throw new Error('인스타그램 문구(caption.txt)가 없습니다');
      if (caption.length > 2200) throw new Error(`인스타그램 문구가 2,200자를 넘습니다(${caption.length}자)`);
      if ((caption.match(/#[^\s#]+/g) || []).length > 30) throw new Error('해시태그가 30개를 넘습니다');
      // 5) n8n 인스타그램 흐름 호출(토큰은 n8n 자격증명에만 있다)
      ctx.act({ k: 'mcp', a: 'n8n 인스타그램 게시' });
      ctx.log(`n8n 게시 요청: 사진 ${urls.length}장${info.dropped.length ? ` (빠진 카드: ${info.dropped.join(', ')})` : ''}`);
      let body = null;
      try {
        const res = await fetch(hook, { method: 'POST', headers: { 'content-type': 'application/json', 'x-office-secret': loadN8nSecret(ctx.cfg) }, body: JSON.stringify({ slug, caption, image_urls: urls }), signal: AbortSignal.timeout(6 * 60000) });
        const t = await res.text();
        try { body = JSON.parse(t); } catch { body = { ok: false, error: t.slice(0, 300) }; }
        if (!res.ok && body.ok !== false) body = { ok: false, error: `HTTP ${res.status} ${t.slice(0, 200)}` };
      } catch (e) { throw new Error(`n8n 인스타그램 흐름에 닿지 못했습니다: ${e.message}`); }
      if (!body?.ok || !body.permalink) throw new Error(`인스타그램 게시 실패: ${body?.error || JSON.stringify(body).slice(0, 300)}`);
      return { summary: `인스타그램에 게시했습니다(${urls.length}장): ${body.permalink}`, outputs: [igDir], result: { slug, permalink: body.permalink, id: body.id, images: urls.length, dropped: info.dropped } };
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
          detail: `${caption}\n\n${r.ok ? '' : `주의: 작업이 정상 종료되지 않았습니다 — ${r.error}\n`}${ctx.cfg.instagram?.enabled && ctx.cfg.n8n?.webhooks?.instagramPublish ? `승인하면 바로 인스타그램에 캐러셀로 게시합니다(4:5 JPEG, 최대 ${Number(ctx.cfg.instagram.maxImages) || 10}장 — 넘으면 앞 장들과 마지막 장). 공개 게시라 되돌리려면 인스타그램에서 직접 지워야 합니다.` : '인스타그램 미연동 — 승인해도 자동 게시하지 않습니다. 압축 파일로 직접 올려 주세요.'}`,
          data: { slug, dest },
        }],
        result: { slug },
      };
    },
  },
];
