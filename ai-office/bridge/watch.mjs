// 폴더 감시 — 설정 watch 의 폴더에 새 파일이 생기면 정해진 작업을 요청한다.
// - 처음 감시를 시작할 때 이미 있던 파일은 '본 것'으로 처리한다(한꺼번에 수십 건이 돌지 않게).
// - OneDrive 동기화 중인 파일을 읽지 않도록, 크기가 두 번 연속 같을 때만 요청한다.
// - 파일을 옮기거나 고치지 않는다(읽기만).
import fs from 'node:fs';
import path from 'node:path';
import { readJsonSafe, writeJsonAtomic } from './util.mjs';
import { currentDeck, deckBase } from './jobs/team2.mjs';

const SKIP = /^(~\$|\.|desktop\.ini$|thumbs\.db$)/i;

export function scanFolder(folder, exts) {
  let names = [];
  try { names = fs.readdirSync(folder, { withFileTypes: true }).filter((d) => d.isFile()).map((d) => d.name); } catch { return null; }
  const out = {};
  for (const n of names) {
    if (SKIP.test(n)) continue;
    if (exts?.length && !exts.includes(path.extname(n).toLowerCase())) continue;
    try { const st = fs.statSync(path.join(folder, n)); out[n] = st.size; } catch { /* 지워짐 */ }
  }
  return out;
}

/** 한 번 살펴보기. state: { [folder]: { seen: {name: size}, pending: {name: size} } } → 새로 요청할 파일 목록 */
export function step(state, w, ignore = () => false) {
  const now = scanFolder(w.folder, w.exts);
  if (now) for (const n of Object.keys(now)) if (ignore(n)) delete now[n];
  if (now === null) return { files: [], missing: true };
  const key = path.resolve(w.folder);
  if (!state[key]) { state[key] = { seen: now, pending: {}, startedAt: new Date().toISOString() }; return { files: [], baseline: Object.keys(now).length }; }
  const st = state[key];
  const ready = [];
  for (const [n, size] of Object.entries(now)) {
    if (Object.hasOwn(st.seen, n)) continue;
    if (st.pending[n] === size && size > 0) { ready.push(n); st.seen[n] = size; delete st.pending[n]; }
    else st.pending[n] = size;
  }
  for (const n of Object.keys(st.pending)) if (!Object.hasOwn(now, n)) delete st.pending[n];
  return { files: ready.map((n) => path.join(w.folder, n)) };
}

export function startWatch({ cfg, paths, runner, store }) {
  const list = (Array.isArray(cfg.watch) ? cfg.watch : []).filter((w) => w && w.enabled !== false && w.folder && w.type);
  if (!list.length) return null;
  const file = path.join(paths.run, 'watch-state.json');
  const state = readJsonSafe(file, {});
  const status = {};
  const tick = () => {
    for (const w of list) {
      // 강사풀 PPT 자신과 그 버전들(…_v6, …_v7)은 강사 프로필이 아니다 → 감시에서 뺀다
      const base = w.type === 'instructor.deck_add' ? deckBase(path.basename(currentDeck(cfg, paths) || '')) : '';
      const r = step(state, w, (n) => !!base && path.extname(n).toLowerCase() === '.pptx' && deckBase(n) === base);
      status[w.folder] = { at: new Date().toISOString(), missing: !!r.missing, baseline: r.baseline };
      if (r.baseline !== undefined) store.event('chief', 'text', `폴더 감시 시작 — 기존 파일 ${r.baseline}개는 건너뜀`);
      for (const f of r.files) {
        try { runner.enqueue(w.type, { ...(w.params || {}), file: f }, { source: 'schedule' }); store.event('chief', 'text', `새 파일 발견: ${path.basename(f)}`); }
        catch (e) { store.event('chief', 'text', `감시 작업 실패: ${e.message}`); }
      }
    }
    writeJsonAtomic(file, state);
  };
  tick();
  const sec = Math.max(30, Math.min(...list.map((w) => Number(w.intervalSec) || 120)));
  const t = setInterval(tick, sec * 1000);
  t.unref?.();
  return { status, list, stop: () => clearInterval(t) };
}
