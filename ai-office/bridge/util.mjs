// 공통 도구: 입력 검증, 경로 안전 검사, JSON 뽑기, 원자적 쓰기, 덮어쓰지 않는 복사.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { IS_WIN } from './config.mjs';

export class InputError extends Error {
  constructor(msg) { super(msg); this.name = 'InputError'; this.status = 400; }
}

export const newId = (prefix = 'J') => {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  const stamp = `${String(d.getFullYear()).slice(2)}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
  return `${prefix}${stamp}-${crypto.randomBytes(3).toString('hex')}`;
};
export const ID_RE = /^[A-Z][0-9]{6}-[0-9]{6}-[0-9a-f]{6}$/;
export const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// 제어문자(줄바꿈·탭 제외) 제거 + 길이 제한
export function cleanText(v, { max = 2000, required = false, label = '값', multiline = true } = {}) {
  if (v === undefined || v === null) v = '';
  if (typeof v !== 'string' && typeof v !== 'number') throw new InputError(`${label}: 글자여야 합니다`);
  let s = String(v).replace(/\r\n?/g, '\n');
  s = s.replace(multiline ? /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g : /[\u0000-\u001F\u007F]/g, '');
  s = s.trim();
  if (required && !s) throw new InputError(`${label}: 비어 있습니다`);
  if (s.length > max) throw new InputError(`${label}: ${max}자 이하로 써 주세요 (지금 ${s.length}자)`);
  return s;
}

export function cleanInt(v, { min, max, def, label = '숫자' } = {}) {
  if (v === undefined || v === null || v === '') return def;
  const n = Number(v);
  if (!Number.isInteger(n) || n < min || n > max) throw new InputError(`${label}: ${min}~${max} 사이 정수`);
  return n;
}

const norm = (p) => (IS_WIN ? p.toLowerCase() : p);
/** child 가 root 안(같거나 아래)인가 — 대소문자(Windows)와 .. 를 정리해서 비교 */
export function isInside(root, child) {
  const r = norm(path.resolve(root));
  const c = norm(path.resolve(child));
  const rel = path.relative(r, c);
  return rel === '' || (!rel.startsWith('..') && !path.isAbsolute(rel));
}

/** 사용자가 넘긴 파일 경로 검사: 절대경로, 허용 폴더 안, 실제 파일, 허용 확장자 */
export function checkInputFile(v, cfg, { exts, label = '파일' } = {}) {
  const s = cleanText(v, { max: 400, required: true, label, multiline: false }).replace(/^"+|"+$/g, '');
  if (!path.isAbsolute(s)) throw new InputError(`${label}: C:\\로 시작하는 전체 경로를 넣어 주세요`);
  const abs = path.resolve(s);
  if (!cfg.inputRoots.some((r) => isInside(r, abs))) {
    throw new InputError(`${label}: 허용된 폴더(${cfg.inputRoots.join(', ')}) 안의 파일만 쓸 수 있습니다`);
  }
  let st;
  try { st = fs.statSync(abs); } catch { throw new InputError(`${label}: 파일이 없습니다 — ${abs}`); }
  if (!st.isFile()) throw new InputError(`${label}: 폴더가 아니라 파일을 넣어 주세요`);
  const ext = path.extname(abs).toLowerCase();
  if (exts && !exts.includes(ext)) throw new InputError(`${label}: ${exts.join(', ')} 파일만 됩니다`);
  return abs;
}

/** 결과 글에서 JSON 한 덩어리 꺼내기: ```json 블록 > 맨 바깥 {…} */
export function extractJson(text) {
  if (!text) return null;
  const blocks = [...String(text).matchAll(/```(?:json)?\s*([\s\S]*?)```/g)].map((m) => m[1]);
  for (const b of blocks.reverse()) {
    try { return JSON.parse(b); } catch { /* 다음 후보 */ }
  }
  const s = String(text);
  const a = s.indexOf('{');
  const z = s.lastIndexOf('}');
  if (a >= 0 && z > a) {
    try { return JSON.parse(s.slice(a, z + 1)); } catch { /* 없음 */ }
  }
  return null;
}

export function writeJsonAtomic(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.${process.pid}.${crypto.randomBytes(3).toString('hex')}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(obj, null, 2), 'utf8');
  fs.renameSync(tmp, file);
}

export function readJsonSafe(file, def = null) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '')); } catch { return def; }
}

/** 같은 이름이 있으면 _2, _3 … 을 붙여 새 파일로 복사(절대 덮어쓰지 않는다) */
export function copyNoOverwrite(src, destFile) {
  fs.mkdirSync(path.dirname(destFile), { recursive: true });
  const ext = path.extname(destFile);
  const stem = destFile.slice(0, destFile.length - ext.length);
  let target = destFile;
  for (let n = 2; fs.existsSync(target); n++) target = `${stem}_${n}${ext}`;
  fs.copyFileSync(src, target, fs.constants.COPYFILE_EXCL);
  return target;
}

export function writeNoOverwrite(destFile, content) {
  fs.mkdirSync(path.dirname(destFile), { recursive: true });
  const ext = path.extname(destFile);
  const stem = destFile.slice(0, destFile.length - ext.length);
  let target = destFile;
  for (let n = 2; fs.existsSync(target); n++) target = `${stem}_${n}${ext}`;
  fs.writeFileSync(target, content, { encoding: 'utf8', flag: 'wx' });
  return target;
}

// Windows 파일 이름에 못 쓰는 글자 정리
export function safeName(s, max = 60) {
  const t = String(s || '').replace(/[\\/:*?"<>|\u0000-\u001F]/g, ' ').replace(/\s+/g, ' ').trim().replace(/[. ]+$/, '');
  return (t || '이름없음').slice(0, max);
}

export const today = () => {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${String(d.getFullYear()).slice(2)}${p(d.getMonth() + 1)}${p(d.getDate())}`;
};

export const cut = (s, n) => {
  const t = String(s ?? '').replace(/\s+/g, ' ').trim();
  return t.length > n ? t.slice(0, n - 1) + '…' : t;
};

/** 외부에서 들어온 글을 프롬프트에 넣을 때 — 지시가 아니라 자료라는 표시로 감싼다 */
export function asData(tag, text) {
  const safe = String(text ?? '').replaceAll(`</${tag}>`, `</ ${tag}>`);
  return `<${tag}>\n${safe}\n</${tag}>`;
}
