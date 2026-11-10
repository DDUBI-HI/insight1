// 강사풀(CSV) — 읽기·중복/변경 판정·반영(승인 후, 백업 먼저)·검증 보고.
// 엑셀에서 바로 열리도록 UTF-8 BOM + 쉼표 구분 CSV 를 쓴다.
import fs from 'node:fs';
import path from 'node:path';
import { copyNoOverwrite, today } from './util.mjs';

export const COLUMNS = ['강사ID', '이름', '이메일', '연락처', '직함', '전문분야', '주요경력', '대표프로그램', '학력', '자격', '요약', '프로필폴더', '출처파일', '최종수정'];
const LIST_SEP = ' / ';

export function parseCsv(text) {
  const s = String(text || '').replace(/^﻿/, '');
  const rows = []; let row = []; let cell = ''; let q = false;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (q) {
      if (c === '"' && s[i + 1] === '"') { cell += '"'; i++; } else if (c === '"') q = false; else cell += c;
    } else if (c === '"') q = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && s[i + 1] === '\n') i++;
      row.push(cell); rows.push(row); row = []; cell = '';
    } else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  return rows.filter((r) => r.some((x) => x.trim() !== ''));
}

const esc = (v) => { const s = String(v ?? ''); return /[",\n\r]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s; };
export const toCsv = (records) => '﻿' + [COLUMNS, ...records.map((r) => COLUMNS.map((c) => r[c] ?? ''))].map((r) => r.map(esc).join(',')).join('\r\n') + '\r\n';

export function readPool(file) {
  if (!fs.existsSync(file)) return [];
  const rows = parseCsv(fs.readFileSync(file, 'utf8'));
  if (!rows.length) return [];
  const head = rows[0].map((h) => h.trim());
  return rows.slice(1).map((r) => Object.fromEntries(head.map((h, i) => [h, (r[i] ?? '').trim()])));
}

export const normName = (s) => String(s || '').replace(/\s+/g, '').replace(/(강사|대표|박사|교수|코치)$/, '');
export const normEmail = (s) => String(s || '').trim().toLowerCase();
export const normPhone = (s) => { const d = String(s || '').replace(/\D/g, ''); return d.length >= 9 ? d : ''; };
const asList = (v) => (Array.isArray(v) ? v : String(v || '').split(/\s*[\/,;\n]\s*/)).map((x) => String(x).trim()).filter(Boolean);

/** Claude 가 뽑은 프로필(JSON) → 강사풀 한 줄 */
export function profileToRecord(p, { folder = '', sourceFile = '' } = {}) {
  return {
    이름: String(p.name || '').trim(),
    이메일: String(p.email || '').trim(),
    연락처: String(p.phone || '').trim(),
    직함: String(p.title || '').trim(),
    전문분야: asList(p.fields).join(LIST_SEP),
    주요경력: asList(p.career).join(LIST_SEP),
    대표프로그램: asList(p.programs).join(LIST_SEP),
    학력: Array.isArray(p.education) ? p.education.join(LIST_SEP) : String(p.education || '').trim(),
    자격: asList(p.certifications).join(LIST_SEP),
    요약: String(p.summary || '').trim().slice(0, 300),
    프로필폴더: folder,
    출처파일: sourceFile,
    최종수정: today(),
  };
}

/** 기존 강사풀에서 같은 사람 찾기. 이메일·연락처가 같으면 같은 사람, 이름만 같으면 '동명이인 의심' */
export function matchRecord(pool, rec) {
  const e = normEmail(rec.이메일); const ph = normPhone(rec.연락처); const n = normName(rec.이름);
  const byContact = pool.find((r) => (e && normEmail(r.이메일) === e) || (ph && normPhone(r.연락처) === ph));
  if (byContact) return { kind: 'same', record: byContact, sameName: normName(byContact.이름) === n };
  const byName = pool.filter((r) => n && normName(r.이름) === n);
  if (byName.length) {
    const noContact = !e && !ph;
    return { kind: noContact ? 'same' : 'namesake', record: byName[0], candidates: byName.length, sameName: true };
  }
  return { kind: 'new', record: null };
}

const DIFF_SKIP = new Set(['강사ID', '최종수정', '프로필폴더', '출처파일']);
// 띄어쓰기·대소문자·전화번호 기호만 다른 것은 바뀐 것으로 보지 않는다
const SAME = { 이름: normName, 이메일: normEmail, 연락처: (v) => normPhone(v) || String(v || '').trim() };
export function diffRecord(oldRec, newRec) {
  const changes = [];
  for (const c of COLUMNS) {
    if (DIFF_SKIP.has(c)) continue;
    const a = String(oldRec?.[c] ?? '').trim(); const b = String(newRec?.[c] ?? '').trim();
    const eq = SAME[c] ? SAME[c](a) === SAME[c](b) : a === b;
    if (b && !eq) changes.push({ field: c, before: a, after: b });
  }
  return changes;
}

const nextId = (pool) => {
  const max = pool.reduce((m, r) => Math.max(m, Number(String(r.강사ID || '').replace(/\D/g, '')) || 0), 0);
  return `T${String(max + 1).padStart(4, '0')}`;
};

/** 변경안 만들기(파일은 안 건드린다) */
export function planUpdate(pool, rec) {
  const m = matchRecord(pool, rec);
  if (m.kind === 'new') return { action: 'add', match: m, record: { ...rec, 강사ID: nextId(pool) }, changes: diffRecord({}, rec) };
  if (m.kind === 'namesake') return { action: 'review', match: m, record: { ...rec, 강사ID: nextId(pool) }, changes: diffRecord({}, rec) };
  const changes = diffRecord(m.record, rec);
  const merged = { ...m.record };
  for (const ch of changes) merged[ch.field] = ch.after;
  merged.최종수정 = rec.최종수정; merged.출처파일 = rec.출처파일 || merged.출처파일; merged.프로필폴더 = rec.프로필폴더 || merged.프로필폴더;
  return { action: changes.length ? 'update' : 'same', match: m, record: merged, changes };
}

/** 승인 후 반영: 기존 파일을 backups 로 먼저 복사하고, 새 내용으로 바꾼다. */
// 'review'(동명이인 의심)를 승인하면 새 강사로 추가한다. 같은 사람이면 반려하고 기존 줄을 직접 고친다.
export function applyUpdate(file, backupDir, plan) {
  const pool = readPool(file);
  let backup = null;
  if (fs.existsSync(file)) backup = copyNoOverwrite(file, path.join(backupDir, `강사풀_${today()}_반영전.csv`));
  const rec = plan.record;
  if (plan.action === 'update' || plan.action === 'same') {
    const i = pool.findIndex((r) => r.강사ID === rec.강사ID);
    if (i >= 0) pool[i] = rec; else pool.push(rec);
  } else {
    if (pool.some((r) => r.강사ID === rec.강사ID)) rec.강사ID = nextId(pool);
    pool.push(rec);
  }
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = file + '.tmp';
  fs.writeFileSync(tmp, toCsv(pool), 'utf8');
  fs.renameSync(tmp, file);
  return { backup, count: pool.length, id: rec.강사ID };
}

/** 강사풀 전체 점검 — 중복·빠진 값·폴더 없음 */
export function verifyPool(file, instructorDirs) {
  const pool = readPool(file);
  const issues = [];
  const seen = { email: new Map(), phone: new Map(), name: new Map() };
  for (const r of pool) {
    const id = r.강사ID || '(ID없음)';
    if (!r.이름) issues.push({ level: '오류', id, msg: '이름이 비어 있습니다' });
    if (!r.이메일 && !r.연락처) issues.push({ level: '주의', id, msg: `${r.이름}: 이메일·연락처가 모두 없어 중복 확인이 어렵습니다` });
    for (const [k, v] of [['email', normEmail(r.이메일)], ['phone', normPhone(r.연락처)], ['name', normName(r.이름)]]) {
      if (!v) continue;
      if (seen[k].has(v)) {
        const other = seen[k].get(v);
        const label = { email: '이메일', phone: '연락처', name: '이름' }[k];
        issues.push({ level: k === 'name' ? '주의' : '오류', id, msg: `${label} 중복: ${other} 와 ${id} (${r.이름})` });
      } else seen[k].set(v, id);
    }
    if (r.프로필폴더 && !fs.existsSync(r.프로필폴더)) issues.push({ level: '주의', id, msg: `${r.이름}: 프로필 폴더가 없습니다 — ${r.프로필폴더}` });
  }
  const folders = fs.existsSync(instructorDirs) ? fs.readdirSync(instructorDirs, { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name) : [];
  const names = new Set(pool.map((r) => normName(r.이름)));
  for (const f of folders) if (!names.has(normName(f))) issues.push({ level: '주의', id: '-', msg: `강사별 폴더 '${f}' 가 강사풀에 없습니다` });
  return { count: pool.length, folders: folders.length, issues };
}
