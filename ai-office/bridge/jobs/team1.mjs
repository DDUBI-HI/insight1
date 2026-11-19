// TEAM 1 · 교육문의·제안팀
// 기존 자산을 그대로 쓴다:
//  - slide-svg/automation/cafe_inquiry (n8n 데이터 표 '제안서_작업대기' → /slide 맞춤본 → n8n 웹훅 검토 메일)
//  - slide-svg/.claude/skills/generic-redesign (고객사 제안서 → 범용본)
// 모든 작업은 slide-svg '복사본'(설정 agents.slideSvg)에서 돈다. 원본 C:\JY\slide-svg 는 건드리지 않는다.
import fs from 'node:fs';
import path from 'node:path';
import { asData, cleanText, copyNoOverwrite, extractJson, safeName, today, writeNoOverwrite, checkInputFile, InputError } from '../util.mjs';
import { COMMON_RULES, lineValue, loadCatalog, requireAgent, slideSvgState } from './common.mjs';

// /slide 파이프라인을 돌리는 작업에 공통으로 주는 허용 도구 (slide-svg 설계 문서 Task 5 의 허용 목록과 같은 범위)
export const SLIDE_ALLOW = [
  'Read', 'Glob', 'Grep', 'Skill', 'TodoWrite',
  'Write(output/**)', 'Edit(output/**)',
  'Bash(.claude/skills/slide/scripts/_py.sh:*)', 'Bash(mkdir:*)', 'Bash(ls:*)', 'Bash(cp:*)',
];
export const SLIDE_DENY = ['Bash(git commit:*)', 'Bash(git push:*)', 'Bash(rm:*)', 'Bash(curl:*)', 'WebFetch'];

const PROPOSAL_EXTS = ['.pptx', '.ppt', '.pdf', '.docx'];

function inquiryFile(paths, jobId) { return path.join(paths.inquiry, `${jobId}.json`); }

function latestExport(projectDir) {
  const dir = path.join(projectDir, 'exports');
  if (!fs.existsSync(dir)) return null;
  const files = fs.readdirSync(dir).filter((f) => f.toLowerCase().endsWith('.pptx') && !/_svg\.pptx$/i.test(f))
    .map((f) => path.join(dir, f));
  if (!files.length) return null;
  return files.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)[0];
}

function newestFile(dir, exts) {
  if (!fs.existsSync(dir)) return null;
  const files = fs.readdirSync(dir).filter((f) => exts.includes(path.extname(f).toLowerCase())).map((f) => path.join(dir, f));
  return files.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)[0] || null;
}

/** 범용화(/generic-redesign) 한 건 — TEAM1(범용본 만들기)과 TEAM2(강사 대표 프로그램 디자인 통일)가 같이 쓴다 */
export async function runGenericRedesign(ctx, { file, dst, reviewKind, reviewTitle, worker }) {
  requireAgent(slideSvgState(ctx.cfg), ctx.cfg);
  fs.mkdirSync(dst, { recursive: true });
  if (ctx.cfg.demo) {
    const out = writeNoOverwrite(path.join(dst, `${safeName(path.parse(file).name)}_범용(데모).txt`), '데모 모드 결과입니다. 실제 PPTX 는 만들지 않았습니다.\n');
    await ctx.claude({ prompt: 'demo', cwd: ctx.emptyDir(), mockTag: 'proposal.generic', allow: [], timeoutMin: 5 });
    return { summary: '(데모) 범용화를 흉내 냈습니다', outputs: [out], approvals: [{ kind: reviewKind, worker, title: reviewTitle, detail: '데모 결과', files: [out] }] };
  }
  const prompt = [
    `다음 제안서 파일을 범용으로 바꿔줘. /generic-redesign 절차(.claude/skills/generic-redesign/SKILL.md)를 그대로 따른다.`,
    `- 원본 파일: ${file}`,
    `- 납품 폴더: 환경변수 GENERIC_REDESIGN_DST (${dst}). finish.py 가 이 폴더로 저장한다.`,
    COMMON_RULES,
    '- 끝나면 마지막 줄에 `OUTPUT: <저장된 pptx 전체 경로>` 를 쓰고, 그 위에 확인 필요 사항(generic-rules §7)을 목록으로 쓴다.',
  ].join('\n');
  const r = await ctx.claude({
    prompt, cwd: ctx.cfg.agents.slideSvg, allow: SLIDE_ALLOW, deny: SLIDE_DENY,
    addDirs: [path.dirname(file), dst], env: { GENERIC_REDESIGN_DST: dst }, timeoutMin: ctx.cfg.limits.jobTimeoutMinutes,
  });
  const reported = lineValue(r.result, 'OUTPUT');
  const pptx = (reported && fs.existsSync(reported)) ? reported : newestFile(dst, ['.pptx']);
  if (!r.ok && !pptx) throw new Error(r.error || '범용화 실패');
  if (!pptx) throw new Error('결과 PPTX 를 찾지 못했습니다. 작업 기록을 확인하세요.');
  const flags = r.result.split('\n').filter((l) => /^\s*[-*]\s/.test(l)).slice(0, 15).join('\n');
  return {
    summary: `범용본을 만들었습니다: ${path.basename(pptx)}`,
    outputs: [pptx],
    approvals: [{ kind: reviewKind, worker, title: reviewTitle, detail: `${flags || '확인 필요 사항 없음'}\n\n권한 거부: ${r.denials.join(', ') || '없음'}`, files: [pptx] }],
  };
}

export const team1Jobs = [
  {
    type: 'inquiry.analyze',
    team: 'team1', worker: 't1-analyst', label: '교육 문의 분석', heavy: false,
    desc: '문의 글을 읽고 대상·일정·인원·니즈·예산을 뽑은 뒤, 범용 제안서 10종 중 맞는 것을 찾습니다. 맞으면 맞춤 초안 만들기를 승인함에 올립니다.',
    fields: [
      { name: 'title', label: '글 제목', kind: 'text', required: true, max: 200 },
      { name: 'body', label: '문의 본문', kind: 'textarea', required: true, max: 8000 },
      { name: 'link', label: '글 주소(선택)', kind: 'text', max: 400 },
      { name: 'boardName', label: '게시판(선택)', kind: 'text', max: 100 },
    ],
    validate: (p) => ({
      title: cleanText(p.title, { max: 200, required: true, label: '글 제목', multiline: false }),
      body: cleanText(p.body, { max: 8000, required: true, label: '문의 본문' }),
      link: cleanText(p.link, { max: 400, label: '글 주소', multiline: false }),
      boardName: cleanText(p.boardName, { max: 100, label: '게시판', multiline: false }),
    }),
    title: (p) => `문의 분석: ${p.title.slice(0, 30)}`,
    async run(ctx) {
      const p = ctx.job.params;
      const catalog = loadCatalog(ctx.cfg);
      if (!catalog.length) throw new Error('범용본 카탈로그(catalog.json)를 읽지 못했습니다. slide-svg 복사본 경로를 확인하세요.');
      const prompt = [
        '너는 인싸이트러닝 교육문의·제안팀의 문의 분석 담당이다. 아래 교육 문의 글에서 정보를 뽑고, 범용 제안서 카탈로그 중 맞는 것을 고른다.',
        '규칙: 글에 없는 값은 null 로 둔다(추측 금지). 강사 섭외만 요청하는 글처럼 제안서가 필요 없는 글은 match.project 를 null 로 둔다.',
        '도구는 쓰지 않는다. 아래 JSON 하나만 출력한다.',
        '```json\n{"summary":"한두 문장 요약","company":null,"target":null,"headcount":null,"schedule":null,"location":null,"format":null,"budget":null,"needs":[],"company_hint":null,"match":{"project":null,"reason":"","confidence":0.0}}\n```',
        COMMON_RULES,
        '## 범용 제안서 카탈로그', JSON.stringify(catalog, null, 1),
        '## 문의 글', asData('external', `제목: ${p.title}\n게시판: ${p.boardName || ''}\n\n${p.body}`),
      ].join('\n\n');
      const r = await ctx.claude({ prompt, cwd: ctx.emptyDir(), allow: [], deny: ['Bash', 'Write', 'Edit', 'WebFetch', 'WebSearch'], timeoutMin: ctx.cfg.limits.lightJobTimeoutMinutes });
      if (!r.ok) throw new Error(r.error);
      const x = extractJson(r.result);
      if (!x || typeof x !== 'object') throw new Error('분석 결과(JSON)를 읽지 못했습니다');
      const match = x.match || {};
      const deck = catalog.find((c) => c.project === match.project);
      const record = { jobId: ctx.job.id, at: new Date().toISOString(), inquiry: p, extracted: x, deck: deck ? deck.deck_file : null };
      const file = writeNoOverwrite(inquiryFile(ctx.paths, ctx.job.id), JSON.stringify(record, null, 2));
      const conf = Number(match.confidence) || 0;
      const approvals = [];
      let summary = `${x.summary || '분석 완료'}`;
      if (deck && conf >= 0.6) {
        summary += ` → 추천 범용본: ${deck.deck_file} (적합도 ${conf.toFixed(2)})`;
        approvals.push({
          kind: 'proposal.draft.confirm', worker: 't1-writer',
          title: `맞춤 초안 만들기 — ${deck.title || deck.deck_file}`,
          detail: [`문의: ${p.title}`, `추천 이유: ${match.reason || ''}`, `대상 ${x.target ?? '명시 없음'} · 인원 ${x.headcount ?? '명시 없음'} · 일정 ${x.schedule ?? '명시 없음'} · 예산 ${x.budget ?? '명시 없음'}`,
            '', '승인하면 /slide 로 맞춤 초안을 만듭니다(30분 안팎, Claude 사용량 큼). 고객사로 자동 발송하지 않습니다.'].join('\n'),
          data: { inquiryJobId: ctx.job.id },
        });
      } else summary += ' → 맞는 범용본 없음(사람이 판단)';
      return { summary, outputs: [file], approvals, result: x };
    },
  },
  {
    type: 'proposal.draft',
    team: 'team1', worker: 't1-writer', label: '맞춤 제안서 초안 만들기', heavy: true, chiefCallable: false,
    desc: '문의 분석 결과로 범용 제안서를 복제해 /slide 수정 모드로 맞춤 초안을 만들고 검토 대기 폴더에 저장합니다.',
    fields: [{ name: 'inquiryJobId', label: '문의 분석 작업 번호', kind: 'text', required: true, max: 40 }],
    validate(p, cfg, store) {
      const id = cleanText(p.inquiryJobId, { max: 40, required: true, label: '문의 분석 작업 번호', multiline: false });
      const j = store?.jobs.get(id);
      if (!j || j.type !== 'inquiry.analyze' || j.status !== 'done') throw new InputError('끝난 문의 분석 작업 번호를 넣어 주세요');
      if (!j.result?.match?.project) throw new InputError('그 문의에는 맞는 범용본이 없습니다');
      return { inquiryJobId: id };
    },
    title: () => '맞춤 제안서 초안',
    async run(ctx) {
      requireAgent(slideSvgState(ctx.cfg), ctx.cfg);
      const src = ctx.store.jobs.get(ctx.job.params.inquiryJobId);
      const x = src.result; const inq = src.params;
      const catalog = loadCatalog(ctx.cfg);
      const deck = catalog.find((c) => c.project === x.match.project);
      const deckName = deck ? path.parse(deck.deck_file).name : x.match.project;
      const articleId = `office-${ctx.job.id}`;
      const outName = `${today()}_${safeName(deckName, 50)}_맞춤초안_${ctx.job.id.slice(-6)}.pptx`;

      if (ctx.cfg.demo) {
        await ctx.claude({ prompt: 'demo', cwd: ctx.emptyDir(), mockTag: 'proposal.draft', allow: [], timeoutMin: 5 });
        const out = writeNoOverwrite(path.join(ctx.paths.review, outName.replace(/\.pptx$/, '(데모).txt')), '데모 모드 결과입니다. 실제 PPTX 는 만들지 않았습니다.\n');
        return { summary: '(데모) 맞춤 초안을 흉내 냈습니다', outputs: [out], approvals: [{ kind: 'proposal.review', worker: 't1-writer', title: `제안서 검토 요청 — ${deckName}`, detail: '데모 결과', files: [out] }] };
      }

      const slide = ctx.cfg.agents.slideSvg;
      const jobJson = path.join(slide, 'output', '_jobs', `${articleId}.json`);
      fs.mkdirSync(path.dirname(jobJson), { recursive: true });
      fs.writeFileSync(jobJson, JSON.stringify({ articleId, title: inq.title, link: inq.link, boardName: inq.boardName, project: x.match.project, extracted: x }, null, 2), 'utf8');
      ctx.log('작업 폴더 준비: automation.cafe_inquiry.jobs prepare');
      const prep = await ctx.python(['-m', 'automation.cafe_inquiry.jobs', 'prepare', '--job-json', jobJson]);
      if (prep.code !== 0) throw new Error(`작업 폴더 준비 실패: ${prep.stderr.slice(-300)}`);
      const projectDir = prep.stdout.trim().split(/\r?\n/).pop();
      const rel = path.relative(slide, projectDir).replaceAll('\\', '/');
      const run = (s) => `.claude/skills/slide/scripts/_py.sh -m automation.cafe_inquiry.run_utf8 .claude/skills/slide/scripts/${s}`;
      const prompt = [
        `이 작업은 사용자가 승인한 기존 덱 기반 수정(/slide revision mode)이다. 새 기획(/slide-plan)은 돌리지 않는다. 확인 게이트는 사전 승인으로 auto-proceed 한다.`,
        `작업 프로젝트: ${rel} (범용본 ${x.match.project} 복제본, sources/inquiry_brief.md 에 문의 요약과 수정 규칙이 있다)`,
        '순서:',
        '1. `.claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/announce_theme.py` 로 활성 테마 확인',
        `2. 읽기: ${rel}/sources/inquiry_brief.md, slide_plan.json, notes/total.md, svg_output/ 목록, .claude/skills/slide/references/executor.md 의 SVG 제약`,
        '3. 고칠 페이지만 svg_output/*.svg 에서 한 페이지씩 순서대로 직접 고친다(서브 에이전트 금지). 페이지 수·파일 이름 유지.',
        '   - 표지·과정 개요: 대상·인원·일정·장소·형태를 추출값으로. 값이 없으면 "협의" 유지',
        '   - 기획 배경: 글의 니즈·상황 반영. 글에 없는 사실은 쓰지 않는다',
        '   - 커리큘럼: 니즈에 맞춰 강조·순서·시간 배분 조정. 새 모듈은 범용본 내용 범위 안에서만',
        '   - 예산: 단가·산정 방식은 그대로. 고객사명은 추출값이 있을 때만, 없으면 "귀사"',
        '   - 바꾸지 않는다: 강사 이력·실적, 회사 소개, 연락처, 테마 디자인',
        '   - 바꾼 페이지의 .gm 한 줄과 notes/total.md 노트도 맞춘다',
        `4. 후처리 — 각각 별도 Bash 호출: \`${run('total_md_split.py')} ${rel}\` → \`${run('finalize_svg.py')} ${rel}\` → \`${run('svg_to_pptx.py')} ${rel} -s final\` → \`${run('verify_deck.py')} ${rel}\` (PASS 필수, 최대 2회 고침)`,
        '5. 눈검수: _pptx_render/*-grid.png 가 있으면 열어 본다. 없으면 바꾼 svg_final/*.svg 를 본다.',
        COMMON_RULES,
        '- n8n 표·웹훅·메일은 건드리지 않는다(이 작업은 AI 사무실 검토 대기 폴더로만 넘긴다).',
        '끝나면 마지막에 두 줄: `CHANGES: 바꾼 내용(페이지 번호와 함께, / 로 구분)` 과 `PENDING: "협의"로 남긴 항목(/ 로 구분)`',
      ].join('\n');
      const r = await ctx.claude({ prompt, cwd: slide, allow: SLIDE_ALLOW, deny: SLIDE_DENY, timeoutMin: ctx.cfg.limits.jobTimeoutMinutes });
      const pptx = latestExport(projectDir);
      if (!pptx) throw new Error(r.ok ? 'exports 에 PPTX 가 없습니다' : r.error);
      const saved = copyNoOverwrite(pptx, path.join(ctx.paths.review, outName));
      const changes = lineValue(r.result, 'CHANGES'); const pending = lineValue(r.result, 'PENDING');
      return {
        summary: `맞춤 초안을 검토 대기 폴더에 저장했습니다: ${path.basename(saved)}`,
        outputs: [saved, projectDir],
        approvals: [{
          kind: 'proposal.review', worker: 't1-writer', title: `제안서 검토 요청 — ${deckName}`, files: [saved],
          detail: [`문의: ${inq.title}`, `바꾼 내용: ${changes || '(보고 없음)'}`, `협의로 남긴 항목: ${pending || '(보고 없음)'}`, `verify/작업 결과: ${r.ok ? '정상 종료' : r.error}`,
            '', '검토 후 "승인"하면 검토완료 폴더로 복사합니다. 고객사 메일 발송은 자동으로 하지 않습니다 — 직접 보내 주세요.'].join('\n'),
        }],
      };
    },
  },
  {
    type: 'inquiry.queue',
    team: 'team1', worker: 't1-writer', label: '인사쟁이 작업대기 처리(기존 n8n 흐름)', heavy: true, chiefCallable: false,
    desc: '기존 n8n 데이터 표 "제안서_작업대기"의 pending 건을 기존 예약 작업 프롬프트 그대로 처리합니다(최대 2건, 검토 메일은 기존 n8n 웹훅이 보냄). Claude 데스크톱 예약 작업과 동시에 돌리지 마세요.',
    fields: [],
    validate: () => ({}),
    title: () => '인사쟁이 작업대기 처리',
    async run(ctx) {
      requireAgent(slideSvgState(ctx.cfg), ctx.cfg);
      let base = 'demo';
      if (!ctx.cfg.demo) {
        const slide = ctx.cfg.agents.slideSvg;
        const pf = path.join(slide, 'automation', 'cafe_inquiry', 'scheduled_task_prompt.md');
        if (!fs.existsSync(pf)) throw new Error(`예약 작업 프롬프트가 없습니다: ${pf}`);
        if (!fs.existsSync(path.join(slide, 'automation', 'cafe_inquiry', '.env'))) throw new Error('automation/cafe_inquiry/.env 가 없습니다(웹훅 주소·비밀값). 원본 C:\\JY\\slide-svg 에서 복사본으로 옮겨 주세요.');
        base = fs.readFileSync(pf, 'utf8');
      }
      const prompt = [
        '[AI 사무실 안내] 이 작업은 AI 사무실 브리지가 실행한다. 작업 폴더는 지금 폴더(C:\\JY\\slide-svg 의 복사본)다. 아래 문서의 "C:\\JY\\slide-svg" 는 지금 폴더로 읽는다.',
        '아래 예약 작업 문서를 처음부터 끝까지 그대로 수행한다.', '', base,
      ].join('\n');
      const r = await ctx.claude({
        prompt, cwd: ctx.cfg.demo ? ctx.emptyDir() : ctx.cfg.agents.slideSvg, mockTag: 'inquiry.queue',
        allow: [...SLIDE_ALLOW, 'mcp__n8n-local__get_data_table_rows', 'mcp__n8n-local__search_data_tables'],
        deny: SLIDE_DENY, timeoutMin: Math.max(120, ctx.cfg.limits.jobTimeoutMinutes),
      });
      if (!r.ok) throw new Error(r.error);
      const lines = r.result.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
      const rows = lines.map((l) => l.match(/^(\S+)\s+(done|failed)\s+(.+)$/)).filter(Boolean);
      const approvals = rows.filter((m) => m[2] === 'done').map((m) => ({
        kind: 'proposal.review', worker: 't1-writer', title: `인사쟁이 문의 ${m[1]} 제안서 초안 검토`,
        detail: `기존 흐름대로 n8n 웹훅이 검토 메일을 보냈습니다(발송 여부는 메일함에서 확인).\n저장 위치: ${m[3]}\n\n고객사 발송은 직접 해 주세요.`,
        files: [m[3]].filter((f) => fs.existsSync(f)),
      }));
      const summary = rows.length ? rows.map((m) => `${m[1]} ${m[2] === 'done' ? '완료' : '실패'}`).join(', ') : (lines.find((l) => l.includes('할 일 없음')) ? '처리할 문의가 없습니다' : lines.slice(-1)[0] || '끝');
      return { summary, approvals, outputs: rows.filter((m) => m[2] === 'done').map((m) => m[3]) };
    },
  },
  {
    type: 'proposal.generic',
    team: 'team1', worker: 't1-writer', label: '고객사 제안서 → 범용본 만들기', heavy: true,
    desc: '고객사용 제안서(PPTX·PPT·PDF·DOCX)를 /generic-redesign 으로 범용본으로 바꿉니다. 원본은 읽기만 하고 결과는 검토 대기 폴더에 저장합니다.',
    fields: [{ name: 'file', label: '원본 파일 전체 경로', kind: 'file', required: true, placeholder: 'C:\\AI-OFFICE\\04_SHARED\\TEST\\제안서.pptx' }],
    validate: (p, cfg) => ({ file: checkInputFile(p.file, cfg, { exts: PROPOSAL_EXTS, label: '원본 파일' }) }),
    title: (p) => `범용본 만들기: ${path.basename(p.file)}`,
    run: (ctx) => runGenericRedesign(ctx, {
      file: ctx.job.params.file,
      dst: path.join(ctx.paths.review, `범용화_${ctx.job.id}`),
      reviewKind: 'proposal.review', worker: 't1-writer',
      reviewTitle: `범용본 검토 요청 — ${path.basename(ctx.job.params.file)}`,
    }),
  },
];
