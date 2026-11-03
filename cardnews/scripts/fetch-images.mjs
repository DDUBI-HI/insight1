#!/usr/bin/env node
// 카드뉴스 덱의 images.json 을 읽어 Unsplash 사진을 images/ 폴더로 내려받습니다.
//
//   node scripts/fetch-images.mjs decks/<deck>          # 없는 사진만 받기
//   node scripts/fetch-images.mjs decks/<deck> --force  # 모두 다시 받기
//   node scripts/fetch-images.mjs                       # decks/ 아래 모든 덱
//
// images.json 항목
//   file      저장할 파일 이름 (index.html 의 <img src="images/..."> 와 같아야 함)
//   unsplash  Unsplash 사진 ID (사진 페이지 URL 끝부분). 비어 있으면 query 로 검색
//   query     검색어. UNSPLASH_ACCESS_KEY 가 있을 때만 사용, 찾은 ID 를 images.json 에 기록
//   author    사진가 이름 (받을 때 자동 기록)
//
// UNSPLASH_ACCESS_KEY 가 있으면 공식 API 를 쓰고(다운로드 집계 포함),
// 없으면 공개 사진 페이지의 다운로드 링크를 씁니다.

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const KEY = process.env.UNSPLASH_ACCESS_KEY || "";
const UA = "insightlearning-cardnews/1.0";

const args = process.argv.slice(2);
const force = args.includes("--force");
let decks = args.filter((a) => !a.startsWith("--")).map((d) => path.resolve(d));
if (decks.length === 0) {
  const base = path.join(ROOT, "decks");
  decks = (await fs.readdir(base, { withFileTypes: true }))
    .filter((d) => d.isDirectory())
    .map((d) => path.join(base, d.name));
}

async function get(url, init = {}) {
  const headers = { "User-Agent": UA, ...(init.headers || {}) };
  if (KEY && url.startsWith("https://api.unsplash.com/")) headers.Authorization = `Client-ID ${KEY}`;
  const res = await fetch(url, { ...init, headers });
  if (!res.ok && !(init.redirect === "manual" && res.status >= 300 && res.status < 400)) {
    throw new Error(`${res.status} ${res.statusText} — ${url}`);
  }
  return res;
}

function sized(rawUrl, width) {
  const u = new URL(rawUrl);
  for (const k of ["dl", "force"]) u.searchParams.delete(k);
  u.searchParams.set("w", String(width));
  u.searchParams.set("q", "82");
  u.searchParams.set("fm", "jpg");
  u.searchParams.set("fit", "max");
  return u.toString();
}

async function searchId(query) {
  if (!KEY) throw new Error(`"${query}": 사진 ID 가 없고 UNSPLASH_ACCESS_KEY 도 없어 검색할 수 없습니다`);
  const q = new URLSearchParams({ query, per_page: "1", content_filter: "high", orientation: "landscape" });
  const json = await (await get(`https://api.unsplash.com/search/photos?${q}`)).json();
  if (!json.results?.length) throw new Error(`"${query}": 검색 결과 없음`);
  return json.results[0].id;
}

// → { url, author, authorUrl }
async function resolve(id, width) {
  if (KEY) {
    const p = await (await get(`https://api.unsplash.com/photos/${encodeURIComponent(id)}`)).json();
    // API 가이드라인: 사진을 쓸 때 download_location 을 호출해 다운로드를 집계합니다.
    await get(p.links.download_location).catch(() => {});
    return { url: sized(p.urls.raw, width), author: p.user?.name, authorUrl: p.user?.links?.html };
  }
  let url = null;
  try {
    const res = await get(`https://unsplash.com/photos/${encodeURIComponent(id)}/download?force=true`, { redirect: "manual" });
    const loc = res.headers.get("location");
    if (loc && new URL(loc).hostname.endsWith("unsplash.com")) url = sized(loc, width);
  } catch { /* 아래 og:image 로 대체 */ }
  if (!url) {
    const html = await (await get(`https://unsplash.com/photos/${encodeURIComponent(id)}`)).text();
    const m = html.match(/<meta[^>]+property="og:image"[^>]+content="([^"]+)"/);
    if (!m) throw new Error(`${id}: 사진 주소를 찾지 못했습니다`);
    url = sized(m[1].replaceAll("&amp;", "&"), width);
  }
  let author, authorUrl;
  try {
    const o = await (await get(`https://unsplash.com/oembed?url=${encodeURIComponent(`https://unsplash.com/photos/${id}`)}`)).json();
    author = o.author_name;
    authorUrl = o.author_url;
  } catch { /* 출처 이름을 못 받아도 사진은 사용 */ }
  return { url, author, authorUrl };
}

let failed = 0;
for (const deck of decks) {
  const manifestPath = path.join(deck, "images.json");
  let manifest;
  try {
    manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
  } catch {
    continue; // images.json 이 없는 덱은 건너뜀
  }
  const width = manifest.width || 1600;
  const dir = path.join(deck, "images");
  await fs.mkdir(dir, { recursive: true });
  console.log(`\n▶ ${path.relative(ROOT, deck)}`);

  for (const item of manifest.images) {
    const dest = path.join(dir, item.file);
    const exists = await fs.stat(dest).then(() => true, () => false);
    if (exists && !force && item.author) {
      console.log(`  · ${item.file} (이미 있음)`);
      continue;
    }
    try {
      if (!item.unsplash) {
        item.unsplash = await searchId(item.query);
        item.page = `https://unsplash.com/photos/${item.unsplash}`;
      }
      const info = await resolve(item.unsplash, width);
      if (!exists || force) {
        const res = await get(info.url);
        const type = res.headers.get("content-type") || "";
        const buf = Buffer.from(await res.arrayBuffer());
        if (!type.startsWith("image/") || buf.length < 10_000) throw new Error(`이미지가 아닌 응답 (${type}, ${buf.length} bytes)`);
        await fs.writeFile(dest, buf);
      }
      if (info.author) item.author = info.author;
      if (info.authorUrl) item.author_url = info.authorUrl;
      console.log(`  ✓ ${item.file} ← ${item.unsplash}${item.author ? ` (${item.author})` : ""}`);
    } catch (err) {
      failed++;
      console.error(`  ✗ ${item.file}: ${err.message}`);
    }
  }

  await fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2) + "\n");
  const rows = manifest.images.map((i) => {
    const who = i.author ? (i.author_url ? `[${i.author}](${i.author_url})` : i.author) : "—";
    const page = i.page || `https://unsplash.com/photos/${i.unsplash}`;
    return `| ${i.card || ""} | \`${i.file}\` | ${who} | [Unsplash](${page}) |`;
  });
  await fs.writeFile(
    path.join(deck, "CREDITS.md"),
    `# 사진 출처\n\n모든 사진은 [Unsplash License](https://unsplash.com/license)에 따라 사용합니다.\n\n| 카드 | 파일 | 사진가 | 원본 |\n|---|---|---|---|\n${rows.join("\n")}\n`,
  );
}

if (failed) {
  console.error(`\n${failed}개 사진을 받지 못했습니다.`);
  process.exit(1);
}
