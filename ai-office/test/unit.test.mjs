// 단위 시험: 입력 검증·경로 안전·JSON 뽑기·강사풀·활동 변환·가짜 Claude 실행
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { checkInputFile, cleanText, copyNoOverwrite, extractJson, isInside, safeName } from '../bridge/util.mjs';
import { applyUpdate, parseCsv, planUpdate, profileToRecord, readPool, toCsv, verifyPool } from '../bridge/instructors.mjs';
import { runClaude, toolAct } from '../bridge/claude.mjs';
import { registry } from '../bridge/jobs/index.mjs';

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'aio-'));

test('isInside: 폴더 밖·.. 경로를 막는다', () => {
  assert.equal(isInside('/a/b', '/a/b/c.txt'), true);
  assert.equal(isInside('/a/b', '/a/b'), true);
  assert.equal(isInside('/a/b', '/a/bc/x'), false);
  assert.equal(isInside('/a/b', '/a/b/../c'), false);
});

test('checkInputFile: 허용 폴더·확장자·실제 파일만', () => {
  const root = tmp();
  const f = path.join(root, '제안서.pptx'); fs.writeFileSync(f, 'x');
  const cfg = { inputRoots: [root] };
  assert.equal(checkInputFile(f, cfg, { exts: ['.pptx'] }), f);
  assert.equal(checkInputFile(`"${f}"`, cfg, { exts: ['.pptx'] }), f, '따옴표 붙은 경로(경로로 복사)도 받는다');
  assert.throws(() => checkInputFile('/etc/passwd', cfg), /허용된 폴더/);
  assert.throws(() => checkInputFile(path.join(root, '..', 'x.pptx'), cfg), /허용된 폴더/);
  assert.throws(() => checkInputFile(path.join(root, '없음.pptx'), cfg), /없습니다/);
  assert.throws(() => checkInputFile(f, cfg, { exts: ['.pdf'] }), /파일만/);
  assert.throws(() => checkInputFile('상대경로.pptx', cfg), /전체 경로/);
});

test('cleanText: 제어문자 제거·길이 제한·필수', () => {
  assert.equal(cleanText(' a\u0000b\n c '), 'ab\n c');
  assert.throws(() => cleanText('', { required: true }), /비어/);
  assert.throws(() => cleanText('x'.repeat(11), { max: 10 }), /10자/);
  assert.equal(cleanText('a\nb', { multiline: false }), 'ab');
});

test('extractJson: 코드 블록 우선, 없으면 바깥 중괄호', () => {
  assert.deepEqual(extractJson('앞말 ```json\n{"a":1}\n``` 뒷말'), { a: 1 });
  assert.deepEqual(extractJson('결과 {"b":[1,2]} 끝'), { b: [1, 2] });
  assert.equal(extractJson('JSON 없음'), null);
});

test('copyNoOverwrite: 같은 이름이면 _2 로 새로 만든다', () => {
  const d = tmp();
  const src = path.join(d, 's.txt'); fs.writeFileSync(src, '새것');
  const dst = path.join(d, 'out', '결과.txt');
  fs.mkdirSync(path.dirname(dst)); fs.writeFileSync(dst, '원본');
  const t = copyNoOverwrite(src, dst);
  assert.equal(path.basename(t), '결과_2.txt');
  assert.equal(fs.readFileSync(dst, 'utf8'), '원본', '원래 파일은 그대로');
  assert.equal(safeName('a/b:c*?'), 'a b c');
});

test('CSV: 쉼표·따옴표·줄바꿈이 있어도 그대로 읽고 쓴다', () => {
  const rec = { 강사ID: 'T0001', 이름: '김, "테스트"', 요약: '첫 줄\n둘째 줄' };
  const rows = parseCsv(toCsv([rec]));
  assert.equal(rows[1][1], '김, "테스트"');
  assert.equal(rows[1][10], '첫 줄\n둘째 줄');
});

test('강사풀: 신규 → 반영 → 같은 프로필은 변경 없음 → 연락처 같으면 갱신 → 이름만 같으면 동명이인', () => {
  const d = tmp();
  const pool = path.join(d, '강사풀.csv'); const backups = path.join(d, 'backups');
  const p1 = profileToRecord({ name: '김테스트', email: 'Kim@Example.com', phone: '010-0000-1234', fields: ['리더십', '코칭'] });
  const plan1 = planUpdate(readPool(pool), p1);
  assert.equal(plan1.action, 'add');
  const r1 = applyUpdate(pool, backups, plan1);
  assert.equal(r1.id, 'T0001'); assert.equal(r1.backup, null);

  const same = planUpdate(readPool(pool), profileToRecord({ name: '김 테스트', email: 'kim@example.com', fields: ['리더십', '코칭'] }));
  assert.equal(same.action, 'same', '공백·대소문자만 다르면 같은 사람, 바뀐 것 없음');

  const upd = planUpdate(readPool(pool), profileToRecord({ name: '김테스트', phone: '01000001234', title: '수석 코치' }));
  assert.equal(upd.action, 'update');
  assert.deepEqual(upd.changes.map((c) => c.field), ['직함']);
  const r2 = applyUpdate(pool, backups, upd);
  assert.ok(r2.backup && fs.existsSync(r2.backup), '반영 전 백업을 만든다');
  assert.equal(readPool(pool).length, 1);
  assert.equal(readPool(pool)[0].직함, '수석 코치');

  const twin = planUpdate(readPool(pool), profileToRecord({ name: '김테스트', email: 'other@example.com' }));
  assert.equal(twin.action, 'review');
  applyUpdate(pool, backups, twin);
  const v = verifyPool(pool, path.join(d, '강사별'));
  assert.equal(v.count, 2);
  assert.ok(v.issues.some((i) => /이름 중복/.test(i.msg)));
});

test('toolAct: 도구 사용을 화면 활동으로 바꾼다', () => {
  assert.deepEqual(toolAct('Read', { file_path: 'C:\\a\\deck.json' }), { k: 'read', a: 'deck.json' });
  assert.deepEqual(toolAct('Bash', { command: 'x', description: 'PPTX 만들기' }), { k: 'bash', a: 'PPTX 만들기' });
  assert.deepEqual(toolAct('mcp__n8n-local__get_data_table_rows', {}), { k: 'mcp', a: 'get_data_table_rows' });
  assert.equal(toolAct('WebFetch', { url: 'https://unsplash.com/x' }).a, 'unsplash.com');
});

test('runClaude(데모): stream-json 을 읽어 결과·세션·활동을 돌려준다, 허용 목록은 설정 파일로만', async () => {
  process.env.AI_OFFICE_MOCK_MS = '5';
  const d = tmp();
  const acts = [];
  const settingsFile = path.join(d, 's.json');
  const r = await runClaude({ demo: true }, { cwd: d, prompt: '안녕', allow: ['Read'], deny: ['Bash'], settingsFile, mockTag: 'cardnews.draft', onAct: (a) => acts.push(a), timeoutMin: 1 });
  assert.equal(r.ok, true);
  assert.match(r.result, /SLUG: 2026-11-demo/);
  assert.match(r.sessionId, /^[0-9a-f-]{36}$/);
  assert.ok(acts.some((a) => a.k === 'read'));
  const s = JSON.parse(fs.readFileSync(settingsFile, 'utf8'));
  assert.deepEqual(s.permissions.allow, ['Read']);
  assert.deepEqual(s.permissions.deny, ['Bash']);
  const bad = await runClaude({ demo: true }, { cwd: d, prompt: 'x', settingsFile, resume: '; rm -rf /' });
  assert.equal(bad.ok, false, '세션 ID 형식이 아니면 실행하지 않는다');
});

test('runClaude: 제한 시간을 넘기면 멈춘다', async () => {
  process.env.AI_OFFICE_MOCK_MS = '3000';
  const d = tmp();
  const t0 = Date.now();
  const r = await runClaude({ demo: true }, { cwd: d, prompt: 'x', settingsFile: path.join(d, 's.json'), timeoutMin: 0.02 });
  process.env.AI_OFFICE_MOCK_MS = '5';
  assert.equal(r.ok, false);
  assert.equal(r.timedOut, true);
  assert.ok(Date.now() - t0 < 8000);
});

test('작업 허용 목록: 모든 작업에 검증·실행·제목이 있고 화면용 목록에는 함수가 없다', () => {
  for (const d of registry.list()) {
    assert.equal(typeof d.validate, 'function', d.type);
    assert.equal(typeof d.run, 'function', d.type);
    assert.equal(typeof d.title, 'function', d.type);
  }
  const pub = JSON.stringify(registry.publicList());
  assert.ok(!pub.includes('function'));
  assert.equal(registry.get('rm -rf'), undefined);
  assert.equal(registry.get('__proto__'), undefined);
});

test('폴더 감시: 처음 있던 파일은 건너뛰고, 새 파일은 크기가 두 번 같을 때만 요청', async () => {
  const { step } = await import('../bridge/watch.mjs');
  const d = tmp();
  fs.writeFileSync(path.join(d, '기존.pdf'), 'a');
  const st = {};
  const w = { folder: d, exts: ['.pdf', '.pptx'] };
  assert.equal(step(st, w).baseline, 1, '처음엔 기준만 잡는다');
  fs.writeFileSync(path.join(d, '신규.pdf'), 'abc');
  fs.writeFileSync(path.join(d, '~$임시.pptx'), 'x');
  fs.writeFileSync(path.join(d, '메모.txt'), 'x');
  assert.deepEqual(step(st, w).files, [], '처음 본 크기 — 아직 동기화 중일 수 있다');
  assert.deepEqual(step(st, w).files.map((f) => path.basename(f)), ['신규.pdf']);
  assert.deepEqual(step(st, w).files, [], '한 번만 요청');
  assert.equal(step(st, { folder: path.join(d, '없음') }).missing, true);
});

test('강사풀 PPT 버전: v6 → v7, 폴더에 더 높은 번호가 있으면 그다음, 감시에서 버전 파일 제외', async () => {
  const { nextVersionPath, deckBase } = await import('../bridge/jobs/team2.mjs');
  const { step } = await import('../bridge/watch.mjs');
  const d = tmp();
  const v6 = path.join(d, '인싸이트러닝_MindAILab_AI-AX_전문강사풀_v6.pptx');
  fs.writeFileSync(v6, 'x');
  assert.equal(path.basename(nextVersionPath(v6)), '인싸이트러닝_MindAILab_AI-AX_전문강사풀_v7.pptx');
  fs.writeFileSync(path.join(d, '인싸이트러닝_MindAILab_AI-AX_전문강사풀_v8.pptx'), 'x');
  assert.equal(path.basename(nextVersionPath(v6)), '인싸이트러닝_MindAILab_AI-AX_전문강사풀_v9.pptx');
  assert.equal(path.basename(nextVersionPath(path.join(d, '강사풀.pptx'))), '강사풀_v2.pptx');
  assert.equal(deckBase('인싸이트러닝_MindAILab_AI-AX_전문강사풀_v12.pptx'), deckBase(v6));
  const st = {};
  const ignore = (n) => deckBase(n) === deckBase(v6);
  step(st, { folder: d, exts: ['.pptx', '.pdf'] }, ignore);
  fs.writeFileSync(path.join(d, '인싸이트러닝_MindAILab_AI-AX_전문강사풀_v9.pptx'), 'x');
  fs.writeFileSync(path.join(d, '홍길동 프로필.pdf'), 'abc');
  step(st, { folder: d, exts: ['.pptx', '.pdf'] }, ignore);
  const r = step(st, { folder: d, exts: ['.pptx', '.pdf'] }, ignore);
  assert.deepEqual(r.files.map((f) => path.basename(f)), ['홍길동 프로필.pdf'], '새 버전 PPT 는 강사 프로필로 보지 않는다');
});
