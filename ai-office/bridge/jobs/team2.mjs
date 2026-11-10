// TEAM 2 · 강사관리팀
// 프로필 읽기는 slide-svg 의 변환기(source_to_md)를 정해진 인자로만 실행하고, 내용 정리는 Claude(도구 없음)가 한다.
// 강사풀 반영은 반드시 승인 후, 기존 파일을 백업한 다음에만 한다.
import fs from 'node:fs';
import path from 'node:path';
import { asData, checkInputFile, cleanText, copyNoOverwrite, extractJson, readJsonSafe, safeName, today, writeJsonAtomic, writeNoOverwrite } from '../util.mjs';
import { ROOT } from '../config.mjs';
import { COMMON_RULES, requireAgent, slideSvgState } from './common.mjs';
import { InputError } from '../util.mjs';
import { planUpdate, profileToRecord, readPool, verifyPool } from '../instructors.mjs';
import { runGenericRedesign } from './team1.mjs';

const CONVERTER = { '.pdf': 'pdf_to_md.py', '.pptx': 'ppt_to_md.py', '.docx': 'doc_to_md.py' };
const MAX_TEXT = 30000;

/** 프로필 파일(PDF·PPTX·DOCX·TXT·MD) → 글자. slide-svg 변환기를 정해진 인자로만 실행한다 */
async function profileText(ctx, file) {
  const ext = path.extname(file).toLowerCase();
  const md = path.join(ctx.dir, 'profile.md');
  if (ext === '.txt' || ext === '.md') fs.copyFileSync(file, md);
  else if (ctx.cfg.demo) fs.writeFileSync(md, '(데모) 프로필 본문', 'utf8');
  else {
    requireAgent(slideSvgState(ctx.cfg), ctx.cfg);
    const script = path.join(ctx.cfg.agents.slideSvg, '.claude', 'skills', 'slide', 'scripts', 'source_to_md', CONVERTER[ext]);
    ctx.log(`글자 뽑기: ${CONVERTER[ext]}`);
    ctx.act({ k: 'read', a: path.basename(file) });
    const r = await ctx.python([script, file, '-o', md]);
    if (r.code !== 0 || !fs.existsSync(md)) throw new Error(`프로필 글자 뽑기 실패: ${(r.stderr || r.stdout).slice(-300)}`);
  }
  return fs.readFileSync(md, 'utf8').slice(0, MAX_TEXT);
}

const DECK_TOOL = path.join(ROOT, 'tools', 'instructor_deck.py');
const currentDeckFile = (paths) => path.join(paths.run, 'instructor-deck-current.json');
/** 지금 기준이 되는 강사풀 PPT: 승인된 최신 버전 > 설정 instructorDeck */
export function currentDeck(cfg, paths) {
  const j = readJsonSafe(currentDeckFile(paths), null);
  if (j?.path && fs.existsSync(j.path)) return j.path;
  return cfg.instructorDeck || '';
}
export function setCurrentDeck(paths, p) { writeJsonAtomic(currentDeckFile(paths), { path: p, at: new Date().toISOString() }); }

async function deckTool(ctx, args) {
  const r = await ctx.python([DECK_TOOL, ...args], { timeoutMin: 15 });
  let j = null;
  try { j = JSON.parse(r.stdout); } catch { /* 아래에서 오류 */ }
  if (!j) throw new Error(`강사풀 PPT 도구 실패: ${(r.stderr || r.stdout).slice(-300)}`);
  return j;
}

function diffTable(plan) {
  const head = { add: '새 강사로 추가합니다', update: '기존 강사 정보를 바꿉니다', review: '이름이 같은 강사가 이미 있습니다(동명이인 의심) — 승인하면 새 강사로 추가합니다', same: '바뀐 내용이 없습니다' }[plan.action];
  const rows = plan.changes.map((c) => `- ${c.field}: ${c.before || '(없음)'} → ${c.after}`);
  return [head, plan.match?.record ? `기존 기록: ${plan.match.record.강사ID} ${plan.match.record.이름}` : '', '', ...(rows.length ? rows : ['- 변경 없음'])].filter((x) => x !== '').join('\n');
}

export const team2Jobs = [
  {
    type: 'instructor.intake',
    team: 'team2', worker: 't2-analyst', label: '신규 강사 프로필 분석', heavy: false,
    desc: '강사 프로필(PDF·PPTX·DOCX)을 읽어 정리하고, 강사별 폴더에 사본을 넣고, 강사풀 반영안(중복·변경 확인)을 승인함에 올립니다.',
    fields: [{ name: 'file', label: '프로필 파일 전체 경로', kind: 'file', required: true, placeholder: 'C:\\AI-OFFICE\\office-data\\04_강사관리\\신규프로필_넣는곳\\홍길동.pdf' }],
    validate: (p, cfg) => ({ file: checkInputFile(p.file, cfg, { exts: Object.keys(CONVERTER).concat(['.txt', '.md']), label: '프로필 파일' }) }),
    title: (p) => `강사 프로필 분석: ${path.basename(p.file)}`,
    async run(ctx) {
      const file = ctx.job.params.file;
      const text = await profileText(ctx, file);
      const prompt = [
        '너는 인싸이트러닝 강사관리팀이다. 아래 강사 프로필 글에서 정보를 뽑아 JSON 하나만 출력한다. 도구는 쓰지 않는다.',
        '규칙: 글에 없는 값은 빈 값으로 둔다(추측 금지). 경력·프로그램은 원문 표현을 짧게 유지한다.',
        '```json\n{"name":"","email":"","phone":"","title":"","fields":[],"career":[],"programs":[],"education":"","certifications":[],"summary":"두 문장 이내"}\n```',
        COMMON_RULES,
        '## 프로필 글', asData('external', text),
      ].join('\n\n');
      const r = await ctx.claude({ prompt, cwd: ctx.emptyDir(), mockTag: 'instructor.intake', allow: [], deny: ['Bash', 'Write', 'Edit', 'WebFetch', 'WebSearch'], timeoutMin: ctx.cfg.limits.lightJobTimeoutMinutes });
      if (!r.ok) throw new Error(r.error);
      const prof = extractJson(r.result);
      if (!prof?.name) throw new Error('강사 이름을 찾지 못했습니다. 프로필 파일을 확인해 주세요.');

      const folder = path.join(ctx.paths.instructorDirs, safeName(prof.name, 40));
      fs.mkdirSync(folder, { recursive: true });
      const copied = copyNoOverwrite(file, path.join(folder, path.basename(file)));
      const profFile = writeNoOverwrite(path.join(folder, `프로필_${today()}.json`), JSON.stringify(prof, null, 2));
      const rec = profileToRecord(prof, { folder, sourceFile: copied });
      const plan = planUpdate(readPool(ctx.paths.instructorPool), rec);
      const approvals = plan.action === 'same' ? [] : [{
        kind: 'instructor.update', worker: 't2-keeper', title: `강사풀 반영 — ${prof.name}`,
        detail: diffTable(plan) + '\n\n승인하면 강사풀.csv 를 백업한 뒤 반영합니다.', data: { plan }, files: [copied, profFile],
      }];
      return {
        summary: `${prof.name}: ${{ add: '신규 강사', update: '정보 변경 있음', review: '동명이인 의심', same: '변경 없음' }[plan.action]} · 강사별 폴더에 정리했습니다`,
        outputs: [folder], approvals, result: { profile: prof, action: plan.action, changes: plan.changes.length },
      };
    },
  },
  {
    type: 'instructor.deck_add',
    team: 'team2', worker: 't2-keeper', label: '강사풀 PPT 에 새 강사 장 추가', heavy: false,
    desc: '강사 프로필을 읽어 강사풀 PPT(예: MindAILab AI/AX 강사풀)와 같은 규격·디자인으로 한 장을 추가하고, 요약표·인원 수·쪽 번호를 맞춘 새 버전을 미리보기와 함께 승인함에 올립니다. 원본 PPT 는 고치지 않습니다.',
    fields: [
      { name: 'file', label: '강사 프로필 파일 전체 경로', kind: 'file', required: true },
      { name: 'deck', label: '강사풀 PPT 경로(비우면 설정값·최신 승인본)', kind: 'file' },
    ],
    validate(p, cfg) {
      const file = checkInputFile(p.file, cfg, { exts: Object.keys(CONVERTER).concat(['.txt', '.md']), label: '프로필 파일' });
      const deck = p.deck ? checkInputFile(p.deck, cfg, { exts: ['.pptx'], label: '강사풀 PPT' }) : '';
      if (!deck && !cfg.instructorDeck && !cfg.demo) throw new InputError('강사풀 PPT 경로를 넣거나 설정 instructorDeck 을 채워 주세요');
      return { file, deck };
    },
    title: (p) => `강사풀 PPT 추가: ${path.basename(p.file)}`,
    async run(ctx) {
      const { file } = ctx.job.params;
      const deck = ctx.job.params.deck || currentDeck(ctx.cfg, ctx.paths);
      const text = await profileText(ctx, file);
      if (ctx.cfg.demo) {
        await ctx.claude({ prompt: 'demo', cwd: ctx.emptyDir(), mockTag: 'instructor.intake', allow: [], timeoutMin: 5 });
        const out = writeNoOverwrite(path.join(ctx.paths.review, `강사풀PPT_강사추가(데모)_${today()}.txt`), '데모 모드 결과입니다. 실제 PPT 는 만들지 않았습니다.\n');
        return { summary: '(데모) 강사풀 PPT 에 강사 장을 추가하는 흐름을 흉내 냈습니다', outputs: [out], approvals: [{ kind: 'deck.update', worker: 't2-keeper', title: '강사풀 PPT 새 버전 확인 — (데모)', detail: '데모 결과', files: [out], data: { out, deck: deck || '(데모)' } }] };
      }
      if (!deck || !fs.existsSync(deck)) throw new Error(`강사풀 PPT 를 찾지 못했습니다: ${deck || '(설정 없음)'}`);
      ctx.act({ k: 'read', a: path.basename(deck) });
      const info = await deckTool(ctx, ['analyze', deck]);
      const f = info.fields;
      const lim = (k, extra = '') => `${k}: 최대 ${f[k].max_lines}줄, 줄당 ${f[k].target_chars}자 안팎(넘어도 ${f[k].max_chars}자까지)${extra}`;
      const ask = (problems, prev) => [
        '너는 인싸이트러닝 강사관리팀이다. 아래 강사 프로필 글을 읽고, 강사풀 PPT 에 들어갈 강사 한 장 분량을 JSON 하나로만 출력한다. 도구는 쓰지 않는다.',
        '규칙:',
        '- 아래 기존 강사 2명의 예시와 같은 말투·길이·형식으로 쓴다(명사형 요약, " · " 로 묶기, 「」 로 과정명).',
        '- 글에 없는 사실·숫자는 쓰지 않는다. 개인 연락처(전화·이메일·주소)는 넣지 않는다(이 PPT 규칙).',
        '- strength_title 은 한 문장 핵심 강점, strength_body 는 2문장 설명.',
        `- education_label 은 ${JSON.stringify(info.education_labels)} 중 내용에 맞는 하나.`,
        `- 칸 한도 — ${lim('affiliation', ' (화면 폭 때문에 2줄로 나누면 줄당 25자 이내)')} / ${lim('specialties')} / ${lim('education')} / ${lim('strength_title')} / ${lim('strength_body')} / ${lim('references', ' (왼쪽·오른쪽 두 단에 나눠 들어감)')} / ${lim('programs')}`,
        '```json\n{"name":"","affiliation":[],"specialties":[],"education_label":"","education":[],"strength_title":"","strength_body":"","references":[],"programs":[]}\n```',
        COMMON_RULES,
        '## 기존 강사 예시', JSON.stringify(info.examples, null, 1),
        ...(problems ? ['## 지난 답의 문제(고쳐서 다시 출력)', problems.join('\n'), '## 지난 답', JSON.stringify(prev)] : []),
        '## 새 강사 프로필 글', asData('external', text),
      ].join('\n\n');
      let prof = null; let res = null; let problems = null;
      for (let attempt = 0; attempt < 2; attempt++) {
        const r = await ctx.claude({ prompt: ask(problems, prof), cwd: ctx.emptyDir(), allow: [], deny: ['Bash', 'Write', 'Edit', 'WebFetch', 'WebSearch'], timeoutMin: ctx.cfg.limits.lightJobTimeoutMinutes });
        if (!r.ok) throw new Error(r.error);
        prof = extractJson(r.result);
        if (!prof?.name) throw new Error('강사 이름을 찾지 못했습니다. 프로필 파일을 확인해 주세요.');
        const pj = path.join(ctx.dir, `deck-profile-${attempt + 1}.json`);
        fs.writeFileSync(pj, JSON.stringify(prof, null, 2), 'utf8');
        const outFile = path.join(ctx.dir, `deck-${attempt + 1}.pptx`);
        res = await deckTool(ctx, ['add', deck, pj, outFile, '--preview', path.join(ctx.dir, 'preview')]);
        if (res.ok || res.code !== 'overflow') break;
        problems = res.problems; ctx.log(`칸 넘침 → 다시 요청: ${problems.join(' / ')}`);
      }
      if (!res.ok) {
        if (res.code === 'exists') return { summary: res.error + ' — 추가하지 않았습니다(갱신은 직접 확인)', result: { name: prof.name, exists: true } };
        throw new Error(`${res.error}${res.problems ? ': ' + res.problems.join(' / ') : ''}`);
      }
      const stem = path.parse(deck).name.replace(/_강사추가_\d{6}.*$/, '');
      const saved = copyNoOverwrite(res.out, path.join(ctx.paths.review, `${stem}_강사추가_${today()}.pptx`));
      // 강사별 폴더 정리 + 강사풀(CSV) 반영안도 함께
      const folder = path.join(ctx.paths.instructorDirs, safeName(prof.name, 40));
      fs.mkdirSync(folder, { recursive: true });
      const copied = copyNoOverwrite(file, path.join(folder, path.basename(file)));
      const rec = profileToRecord({ name: prof.name, title: (prof.affiliation || [])[0], fields: prof.specialties, career: prof.references, programs: prof.programs, education: prof.education, summary: prof.strength_title }, { folder, sourceFile: copied });
      const plan = planUpdate(readPool(ctx.paths.instructorPool), rec);
      const previews = (res.preview || []).filter((x) => fs.existsSync(x));
      const approvals = [{
        kind: 'deck.update', worker: 't2-keeper', title: `강사풀 PPT 새 버전 확인 — ${prof.name} 추가`,
        files: [saved, ...previews],
        detail: [`기준 파일: ${deck}`, `새 장: ${res.new_slide}장 (${prof.name}) · 전체 ${res.count}명`, `${res.summary} · 인원 수를 고친 장: ${res.count_changed_slides.join(', ')} · 쪽 번호 ${res.renumbered}곳`,
          previews.length ? '미리보기 그림을 눌러 디자인을 확인하세요.' : '미리보기를 만들지 못했습니다 — PPTX 를 열어 확인하세요.',
          '', '승인하면 원본 옆에 새 버전 파일로 저장합니다(원본은 그대로). 다음 강사는 이 새 버전에 이어서 추가합니다.'].join('\n'),
        data: { out: saved, deck },
      }];
      if (plan.action !== 'same') approvals.push({ kind: 'instructor.update', worker: 't2-keeper', title: `강사풀 반영 — ${prof.name}`, detail: diffTable(plan) + '\n\n승인하면 강사풀.csv 를 백업한 뒤 반영합니다.', data: { plan }, files: [copied] });
      return { summary: `${prof.name} 강사 장을 추가한 새 버전을 만들었습니다(${res.new_slide}장, 전체 ${res.count}명)`, outputs: [saved, folder, ...previews], approvals, result: { name: prof.name, slide: res.new_slide, count: res.count } };
    },
  },
  {
    type: 'instructor.verify',
    team: 'team2', worker: 't2-keeper', label: '강사풀 중복·변경 검증', heavy: false,
    desc: '강사풀.csv 전체에서 이메일·연락처·이름 중복, 빠진 값, 폴더 불일치를 찾아 보고서를 만듭니다(Claude 사용량 없음, 파일 수정 없음).',
    fields: [],
    validate: () => ({}),
    title: () => '강사풀 검증',
    async run(ctx) {
      ctx.act({ k: 'read', a: '강사풀.csv' });
      const v = verifyPool(ctx.paths.instructorPool, ctx.paths.instructorDirs);
      const md = [
        `# 강사풀 점검 (${new Date().toLocaleString('ko-KR')})`, '',
        `- 강사 ${v.count}명, 강사별 폴더 ${v.folders}개, 발견 ${v.issues.length}건`, '',
        '| 수준 | 강사ID | 내용 |', '|---|---|---|',
        ...(v.issues.length ? v.issues.map((i) => `| ${i.level} | ${i.id} | ${i.msg.replaceAll('|', '/')} |`) : ['| - | - | 문제 없음 |']),
      ].join('\n');
      const file = writeNoOverwrite(path.join(ctx.paths.reports, `강사풀점검_${today()}.md`), md);
      const err = v.issues.filter((i) => i.level === '오류').length;
      return { summary: `강사 ${v.count}명 점검: 오류 ${err}건, 주의 ${v.issues.length - err}건`, outputs: [file], result: v };
    },
  },
  {
    type: 'instructor.redesign',
    team: 'team2', worker: 't2-keeper', label: '대표 프로그램 제안서 디자인 통일', heavy: true,
    desc: '강사의 대표 프로그램 제안서를 /generic-redesign 으로 인싸이트러닝 테마 범용본으로 바꿔 강사별 폴더에 저장합니다.',
    fields: [
      { name: 'file', label: '대표 프로그램 제안서 전체 경로', kind: 'file', required: true },
      { name: 'name', label: '강사 이름', kind: 'text', required: true, max: 40 },
    ],
    validate: (p, cfg) => ({
      file: checkInputFile(p.file, cfg, { exts: ['.pptx', '.ppt', '.pdf', '.docx'], label: '제안서 파일' }),
      name: cleanText(p.name, { max: 40, required: true, label: '강사 이름', multiline: false }),
    }),
    title: (p) => `디자인 통일: ${p.name} — ${path.basename(p.file)}`,
    run: (ctx) => runGenericRedesign(ctx, {
      file: ctx.job.params.file,
      dst: path.join(ctx.paths.instructorDirs, safeName(ctx.job.params.name, 40), '대표프로그램_디자인통일'),
      reviewKind: 'design.review', worker: 't2-keeper',
      reviewTitle: `디자인 통일 결과 확인 — ${ctx.job.params.name}`,
    }),
  },
];
