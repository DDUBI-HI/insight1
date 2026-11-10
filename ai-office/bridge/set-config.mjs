#!/usr/bin/env node
// config.json 의 강사풀 PPT·폴더 감시 설정을 바꾼다(바꾸기 전 config.json.bak-<시각> 으로 백업).
//   node bridge/set-config.mjs --deck "C:\...\강사풀.pptx" --watch "C:\...\05. AI.AX.DX 신규 강사"
//   node bridge/set-config.mjs --watch-off        (폴더 감시 끄기)
import fs from 'node:fs';
import path from 'node:path';
import { ROOT } from './config.mjs';

const file = path.join(ROOT, 'config.json');
const src = fs.existsSync(file) ? file : path.join(ROOT, 'config.example.json');
const cfg = JSON.parse(fs.readFileSync(src, 'utf8').replace(/^\uFEFF/, ''));
const arg = (k) => { const i = process.argv.indexOf(k); return i >= 0 ? process.argv[i + 1] : undefined; };
const clean = (p) => String(p || '').trim().replace(/^"+|"+$/g, '');
const msgs = [];

const deck = arg('--deck');
if (deck !== undefined) {
  const p = clean(deck);
  if (!/\.pptx$/i.test(p) || !fs.existsSync(p)) { console.error(`[실패] PPTX 파일을 찾지 못했습니다: ${p}`); process.exit(1); }
  cfg.instructorDeck = p; msgs.push(`강사풀 PPT: ${p}`);
}
const watch = arg('--watch');
if (watch !== undefined) {
  const p = clean(watch);
  if (!fs.existsSync(p) || !fs.statSync(p).isDirectory()) { console.error(`[실패] 폴더를 찾지 못했습니다: ${p}`); process.exit(1); }
  const list = (Array.isArray(cfg.watch) ? cfg.watch : []).filter((w) => w.type !== 'instructor.deck_add');
  list.push({ enabled: true, folder: p, type: 'instructor.deck_add', exts: ['.pdf', '.pptx', '.docx'], intervalSec: 120 });
  cfg.watch = list; msgs.push(`폴더 감시(2분마다): ${p}`);
}
if (process.argv.includes('--watch-off')) {
  cfg.watch = (Array.isArray(cfg.watch) ? cfg.watch : []).map((w) => (w.type === 'instructor.deck_add' ? { ...w, enabled: false } : w));
  msgs.push('강사 폴더 감시를 껐습니다');
}
if (!msgs.length) { console.log('바꿀 것이 없습니다. --deck "<PPTX 경로>" --watch "<폴더 경로>" 를 넣어 주세요.'); process.exit(0); }
if (fs.existsSync(file)) fs.copyFileSync(file, `${file}.bak-${new Date().toISOString().replace(/[:.]/g, '-')}`);
fs.writeFileSync(file, JSON.stringify(cfg, null, 2) + '\n', 'utf8');
for (const m of msgs) console.log(`[완료] ${m}`);
console.log('STOP-AI-OFFICE.bat → START-AI-OFFICE.bat 로 다시 켜면 적용됩니다.');
