// 설정 읽기 + 브리지 토큰 준비.
// 설정 파일: ai-office/config.json (없으면 config.example.json 기본값). 토큰은 설정 파일이나 코드에 두지 않고
// <dataDir>/secret/bridge-token.txt 에 처음 실행 때 만든다(또는 환경변수 AI_OFFICE_TOKEN).
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const APP = 'ai-office';
export const VERSION = '0.1.0';
export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const IS_WIN = process.platform === 'win32';

const DEFAULTS = {
  port: 8765,
  bindHost: '127.0.0.1',
  extraHosts: [],
  dataDir: IS_WIN ? 'C:\\AI-OFFICE\\office-data' : path.join(ROOT, '.office-data'),
  claudePath: 'claude',
  // 설정 파일에 없으면 설치 스크립트가 만드는 기본 위치를 쓴다
  agents: IS_WIN ? { slideSvg: 'C:\\AI-OFFICE\\agents\\slide-svg', cardnews: 'C:\\AI-OFFICE\\agents\\insight1-cardnews' } : { slideSvg: '', cardnews: '' },
  inputRoots: [],
  // 강사풀 PPT(새 강사 장을 추가할 원본). 원본은 고치지 않고 승인 후 새 버전 파일로 저장한다
  instructorDeck: '',
  // 폴더 감시: [{ enabled, folder, type, exts, intervalSec }] — 새 파일이 생기면 그 작업을 요청
  watch: [],
  n8n: { baseUrl: 'http://localhost:5678', webhooks: { events: '', instagramPublish: '' } },
  instagram: { enabled: false },
  limits: { jobTimeoutMinutes: 90, lightJobTimeoutMinutes: 20 },
  schedule: [],
  demo: false,
  lang: 'ko',
};

function merge(base, over) {
  if (!over || typeof over !== 'object' || Array.isArray(over)) return over === undefined ? base : over;
  const out = { ...base };
  for (const [k, v] of Object.entries(over)) {
    out[k] = base && typeof base[k] === 'object' && !Array.isArray(base[k]) && base[k] !== null ? merge(base[k], v) : v;
  }
  return out;
}

function readJson(file) {
  const raw = fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '');
  return JSON.parse(raw);
}

/** 설정을 읽는다. opts.file 로 다른 파일, opts.override 로 일부 값 덮어쓰기(시험·데모용). */
export function loadConfig(opts = {}) {
  let fileCfg = {};
  const file = opts.file || process.env.AI_OFFICE_CONFIG || path.join(ROOT, 'config.json');
  if (fs.existsSync(file)) fileCfg = readJson(file);
  let cfg = merge(DEFAULTS, fileCfg);
  if (opts.override) cfg = merge(cfg, opts.override);
  if (process.env.AI_OFFICE_PORT) cfg.port = Number(process.env.AI_OFFICE_PORT);
  if (process.env.AI_OFFICE_DATA) cfg.dataDir = process.env.AI_OFFICE_DATA;
  if (process.env.AI_OFFICE_DEMO === '1') cfg.demo = true;
  cfg.dataDir = path.resolve(cfg.dataDir);
  if (!Array.isArray(cfg.inputRoots) || !cfg.inputRoots.length) cfg.inputRoots = [path.dirname(cfg.dataDir)];
  // 감시 폴더와 강사풀 PPT 폴더의 파일도 받을 수 있게 한다
  for (const w of Array.isArray(cfg.watch) ? cfg.watch : []) if (w && w.folder) cfg.inputRoots.push(w.folder);
  if (cfg.instructorDeck) cfg.inputRoots.push(path.dirname(cfg.instructorDeck));
  cfg.inputRoots = [...new Set(cfg.inputRoots.map((p) => path.resolve(p)))];
  cfg.configFile = fs.existsSync(file) ? file : null;
  return cfg;
}

/** 데이터 폴더 구조. 모든 업무 결과는 여기 아래 새 파일로만 만든다(기존 파일 덮어쓰기 없음). */
export function dataPaths(cfg) {
  const d = cfg.dataDir;
  return {
    root: d,
    secret: path.join(d, 'secret'),
    jobs: path.join(d, 'jobs'),
    run: path.join(d, 'run'),
    logs: path.join(d, 'logs'),
    reports: path.join(d, 'reports'),
    backups: path.join(d, 'backups'),
    inquiry: path.join(d, '01_교육문의'),
    review: path.join(d, '02_제안서_검토대기'),
    approved: path.join(d, '03_제안서_검토완료'),
    instructors: path.join(d, '04_강사관리'),
    instructorInbox: path.join(d, '04_강사관리', '신규프로필_넣는곳'),
    instructorDirs: path.join(d, '04_강사관리', '강사별'),
    instructorPool: path.join(d, '04_강사관리', '강사풀.csv'),
    content: path.join(d, '05_콘텐츠'),
    trends: path.join(d, '05_콘텐츠', '트렌드'),
    cardnews: path.join(d, '05_콘텐츠', '카드뉴스'),
  };
}

export function ensureDirs(cfg) {
  const p = dataPaths(cfg);
  for (const [k, v] of Object.entries(p)) {
    if (k === 'instructorPool') continue;
    fs.mkdirSync(v, { recursive: true });
  }
  return p;
}

/** 토큰: 환경변수 > 파일 > 새로 만들기(파일 권한은 OS 기본, 화면·로그에 출력하지 않는다) */
export function loadToken(cfg) {
  if (process.env.AI_OFFICE_TOKEN && process.env.AI_OFFICE_TOKEN.length >= 24) return process.env.AI_OFFICE_TOKEN;
  const p = dataPaths(cfg);
  const file = path.join(p.secret, 'bridge-token.txt');
  if (fs.existsSync(file)) {
    const t = fs.readFileSync(file, 'utf8').trim();
    if (t.length >= 24) return t;
  }
  fs.mkdirSync(p.secret, { recursive: true });
  const t = crypto.randomBytes(32).toString('base64url');
  fs.writeFileSync(file, t + '\n', { encoding: 'utf8', mode: 0o600 });
  return t;
}

/** n8n 웹훅(작업 알림)용 비밀값 — <dataDir>/secret/n8n-webhook-secret.txt. 사용자가 이 값을 n8n Header Auth 자격증명에 넣는다. */
export function loadN8nSecret(cfg) {
  const p = dataPaths(cfg);
  const file = path.join(p.secret, 'n8n-webhook-secret.txt');
  if (fs.existsSync(file)) {
    const t = fs.readFileSync(file, 'utf8').trim();
    if (t.length >= 24) return t;
  }
  fs.mkdirSync(p.secret, { recursive: true });
  const t = crypto.randomBytes(32).toString('base64url');
  fs.writeFileSync(file, t + '\n', { encoding: 'utf8', mode: 0o600 });
  return t;
}
