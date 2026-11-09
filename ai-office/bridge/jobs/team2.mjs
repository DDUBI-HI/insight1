// TEAM 2 · 강사관리팀
// 프로필 읽기는 slide-svg 의 변환기(source_to_md)를 정해진 인자로만 실행하고, 내용 정리는 Claude(도구 없음)가 한다.
// 강사풀 반영은 반드시 승인 후, 기존 파일을 백업한 다음에만 한다.
import fs from 'node:fs';
import path from 'node:path';
import { asData, checkInputFile, cleanText, copyNoOverwrite, extractJson, safeName, today, writeNoOverwrite } from '../util.mjs';
import { COMMON_RULES, requireAgent, slideSvgState } from './common.mjs';
import { planUpdate, profileToRecord, readPool, verifyPool } from '../instructors.mjs';
import { runGenericRedesign } from './team1.mjs';

const CONVERTER = { '.pdf': 'pdf_to_md.py', '.pptx': 'ppt_to_md.py', '.docx': 'doc_to_md.py' };
const MAX_TEXT = 30000;

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
      const text = fs.readFileSync(md, 'utf8').slice(0, MAX_TEXT);
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
