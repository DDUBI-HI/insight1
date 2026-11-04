#!/usr/bin/env node
// 덱 결과물을 한 번에 전달할 압축 파일로 묶습니다.
//
//   node scripts/pack-deck.mjs decks/<slug>     # → dist/<slug>.zip
//   node scripts/pack-deck.mjs                  # decks/ 아래 렌더된 모든 덱
//
// 압축 파일 안: <slug>/01-….png … 13-….png (업로드 순서), caption.txt (인스타그램 문구), CREDITS.md (사진 출처)
// PNG 는 이미 압축된 형식이라 무압축(store)으로 묶습니다. 외부 zip 프로그램 없이 어느 OS 에서나 동작합니다.
// dist/ 는 커밋하지 않습니다 (.gitignore).

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DIST = path.join(ROOT, "dist");

let decks = process.argv.slice(2).map((d) => path.resolve(d));
const explicit = decks.length > 0;
if (!explicit) {
  const base = path.join(ROOT, "decks");
  decks = (await fs.readdir(base, { withFileTypes: true }))
    .filter((d) => d.isDirectory())
    .map((d) => path.join(base, d.name));
}

// CRC-32 (zip 표준 다항식)
const CRC_TABLE = Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
function crc32(buf) {
  let c = 0xffffffff;
  for (const b of buf) c = CRC_TABLE[(c ^ b) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function dosTime(d) {
  const time = (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1);
  const date = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();
  return { time, date };
}

// entries: [{ name, data }] → 무압축 zip Buffer
function zip(entries) {
  const { time, date } = dosTime(new Date());
  const locals = [];
  const centrals = [];
  let offset = 0;
  for (const { name, data } of entries) {
    const nameBuf = Buffer.from(name, "utf8");
    const crc = crc32(data);
    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0);
    local.writeUInt16LE(20, 4);       // version needed
    local.writeUInt16LE(0x0800, 6);   // UTF-8 파일 이름
    local.writeUInt16LE(0, 8);        // store
    local.writeUInt16LE(time, 10);
    local.writeUInt16LE(date, 12);
    local.writeUInt32LE(crc, 14);
    local.writeUInt32LE(data.length, 18);
    local.writeUInt32LE(data.length, 22);
    local.writeUInt16LE(nameBuf.length, 26);
    local.writeUInt16LE(0, 28);
    locals.push(local, nameBuf, data);

    const central = Buffer.alloc(46);
    central.writeUInt32LE(0x02014b50, 0);
    central.writeUInt16LE(20, 4);     // version made by
    central.writeUInt16LE(20, 6);
    central.writeUInt16LE(0x0800, 8);
    central.writeUInt16LE(0, 10);
    central.writeUInt16LE(time, 12);
    central.writeUInt16LE(date, 14);
    central.writeUInt32LE(crc, 16);
    central.writeUInt32LE(data.length, 20);
    central.writeUInt32LE(data.length, 24);
    central.writeUInt16LE(nameBuf.length, 28);
    central.writeUInt32LE(offset, 42);
    centrals.push(central, nameBuf);
    offset += local.length + nameBuf.length + data.length;
  }
  const centralSize = centrals.reduce((n, b) => n + b.length, 0);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(entries.length, 8);
  end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(centralSize, 12);
  end.writeUInt32LE(offset, 16);
  return Buffer.concat([...locals, ...centrals, end]);
}

await fs.mkdir(DIST, { recursive: true });
let failed = false;
let packed = 0;
for (const deck of decks) {
  const slug = path.basename(deck);
  const out = path.join(deck, "out");
  const pngs = (await fs.readdir(out).catch(() => []))
    .filter((f) => /^\d{2}-.+\.png$/.test(f))
    .sort();
  if (pngs.length === 0) {
    if (explicit) {
      console.error(`✗ ${slug}: 렌더된 카드가 없습니다 (out/ 확인, 렌더 커밋을 pull 했는지 확인)`);
      failed = true;
    }
    continue;
  }
  const entries = [];
  for (const f of pngs) entries.push({ name: `${slug}/${f}`, data: await fs.readFile(path.join(out, f)) });
  for (const f of ["caption.txt", "CREDITS.md"]) {
    const data = await fs.readFile(path.join(deck, f)).catch(() => null);
    if (data) entries.push({ name: `${slug}/${f}`, data });
    else console.warn(`  ! ${slug}: ${f} 가 없어 빼고 묶습니다`);
  }
  const file = path.join(DIST, `${slug}.zip`);
  const buf = zip(entries);
  await fs.writeFile(file, buf);
  packed++;
  console.log(`✓ ${path.relative(process.cwd(), file)} — 카드 ${pngs.length}장 + ${entries.length - pngs.length}개 파일, ${(buf.length / 1024 / 1024).toFixed(1)}MB`);
}
if (!packed && !failed) console.error("묶을 덱이 없습니다");
process.exit(failed || !packed ? 1 : 0);
