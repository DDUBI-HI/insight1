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
//   query     검색어. unsplash 가 비어 있으면 1순위 결과를 골라 ID 를 images.json 에 기록
//   author    사진가 이름 (받을 때 자동 기록)
//
// 공식 Unsplash API 를 쓰므로 UNSPLASH_ACCESS_KEY (무료 개발자 키) 가 필요합니다.
// 사진을 쓸 때마다 API 가이드라인대로 download_location 을 호출해 다운로드를 집계합니다.

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
  if (!res.ok) {
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
  const q = new URLSearchParams({ query, per_page: "1", content_filter: "high", orientation: "landscape" });
  const json = await (await get(`https://api.unsplash.com/search/photos?${q}`)).json();
  if (!json.results?.length) throw new Error(`"${query}": 검색 결과 없음`);
  return json.results[0].id;
}

// 공식 Unsplash API 로 사진 정보를 가져옵니다 → { url, author, authorUrl }
async function resolve(id, width) {
  const p = await (await get(`https://api.unsplash.com/photos/${encodeURIComponent(id)}`)).json();
  // API 가이드라인: 사진을 쓸 때 download_location 을 호출해 다운로드를 집계합니다.
  await get(p.links.download_location).catch(() => {});
  return { url: sized(p.urls.raw, width), author: p.user?.name, authorUrl: p.user?.links?.html };
}

if (!KEY) {
  console.error(
    "UNSPLASH_ACCESS_KEY 가 없습니다.\n" +
    "  1) https://unsplash.com/oauth/applications 에서 앱을 만들고 Access Key 를 복사합니다.\n" +
    "  2) 로컬: UNSPLASH_ACCESS_KEY=... npm run fetch\n" +
    "     GitHub Actions: 저장소 Settings → Secrets and variables → Actions 에 UNSPLASH_ACCESS_KEY 로 등록합니다.",
  );
  process.exit(1);
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
