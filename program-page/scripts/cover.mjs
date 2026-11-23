#!/usr/bin/env node
// 교육 프로그램 표지 카드(1:1): page.json 의 "cover" → cover.html → <name>_표지.png
//
//   node program-page/scripts/cover.mjs <page.json> [--scale 2] [--out dir] [--strict]
//
// page.json 에 다음을 넣습니다 (title 이 없으면 page.json 의 title 을 씁니다).
//   "cover": {
//     "title": "Claude 기반\nAI Agent 실무 활용 과정",   // 2줄 이내, \n 으로 직접 끊기
//     "subtitle": "실무에 적용하는 Live Data 기반\nAI Agent 활용 과정", // 2줄 이내
//     "image": "img/cover.jpg",                          // page.json 기준 상대 경로
//     "position": "center 40%"                           // 선택: 사진 자르는 기준점 (CSS object-position)
//   }
// build.mjs 는 cover 가 있으면 이 스크립트를 함께 실행합니다.

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PP = path.resolve(HERE, "..");
const ROOT = path.resolve(PP, "..");
const FONT = path.join(ROOT, "fonts", "PretendardVariable.woff2");

const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const lines = (s) => esc(s).replace(/\n/g, "<br>");
const ARROW = `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.5 4.5l7.5 7.5-7.5 7.5"/></svg>`;

// 표지를 렌더하고 경고 목록을 돌려줍니다. 브라우저는 호출한 쪽이 엽니다.
export async function renderCover({ browser, spec, specDir, outDir, scale = 2 }) {
  const warns = [];
  const c = spec.cover;
  const title = c.title || spec.title;
  if (!c.subtitle) warns.push("[표지] subtitle 이 비어 있습니다");
  let photo = `<div class="cv-photo missing">사진</div>`;
  if (c.image) {
    const abs = path.resolve(specDir, c.image);
    const pos = c.position ? ` style="object-position:${esc(c.position)}"` : "";
    photo = `<div class="cv-photo"><img src="${pathToFileURL(abs).href}" data-src="${esc(c.image)}"${pos} alt=""></div>`;
  } else warns.push("[표지] image 가 없어 회색 자리 표시로 렌더했습니다");

  const css = (await fs.readFile(path.join(PP, "cover.css"), "utf8")).replaceAll("__FONT_URL__", pathToFileURL(FONT).href);
  const html = `<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>${esc(title)}</title><style>${css}</style></head>
<body><main class="cv" id="cover">${photo}
<h1 class="cv-title">${lines(title)}</h1>
<p class="cv-sub">${lines(c.subtitle)}</p>
<span class="cv-go">${ARROW}</span>
</main></body></html>`;
  const htmlPath = path.join(outDir, "cover.html");
  await fs.writeFile(htmlPath, html);

  const page = await browser.newPage({ viewport: { width: 540, height: 540 }, deviceScaleFactor: scale });
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  const r = await page.evaluate(() => {
    const n = (el) => {
      const rg = document.createRange(); rg.selectNodeContents(el);
      return new Set([...rg.getClientRects()].filter((x) => x.width > 1).map((x) => Math.round(x.top))).size;
    };
    const t = document.querySelector(".cv-title"), s = document.querySelector(".cv-sub"), go = document.querySelector(".cv-go");
    const sb = s.getBoundingClientRect(), gb = go.getBoundingClientRect(), tb = t.getBoundingClientRect();
    const img = document.querySelector(".cv-photo img");
    return {
      titleLines: n(t), subLines: n(s),
      overlap: tb.bottom > sb.top + 2, cut: sb.bottom > 540 - 8,
      broken: img && (!img.complete || img.naturalWidth === 0) ? img.dataset.src : null,
    };
  });
  if (r.titleLines > 2) warns.push(`[표지] 제목이 ${r.titleLines}줄입니다 — 2줄 이내로 줄이거나 \\n 위치를 바꾸세요`);
  if (r.subLines > 2) warns.push(`[표지] 부제가 ${r.subLines}줄입니다 — 2줄 이내로 줄이세요`);
  if (r.overlap) warns.push("[표지] 제목과 부제가 겹칩니다");
  if (r.cut) warns.push("[표지] 부제가 카드 아래로 넘칩니다");
  if (r.broken) warns.push(`[표지] 사진을 불러오지 못했습니다: ${r.broken}`);

  const name = (spec.name || "page").replace(/[\\/:*?"<>|]/g, "_");
  const pngPath = path.join(outDir, `${name}_표지.png`);
  await (await page.$("#cover")).screenshot({ path: pngPath });
  await page.close();
  return { pngPath, warns, size: 540 * scale };
}

// ── 단독 실행 ─────────────────────────────────────────
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  let specPath = null, scale = 2, out = null, strict = false;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--scale") scale = Number(args[++i]);
    else if (args[i] === "--out") out = args[++i];
    else if (args[i] === "--strict") strict = true;
    else specPath = args[i];
  }
  if (!specPath) { console.error("사용법: node program-page/scripts/cover.mjs <page.json> [--scale 2] [--out dir] [--strict]"); process.exit(1); }
  specPath = path.resolve(specPath);
  const spec = JSON.parse(await fs.readFile(specPath, "utf8"));
  if (!spec.cover) { console.error("✗ page.json 에 cover 가 없습니다"); process.exit(1); }
  const specDir = path.dirname(specPath), outDir = path.resolve(out || specDir);
  await fs.mkdir(outDir, { recursive: true });
  const { chromium } = createRequire(import.meta.url)("playwright");
  const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  try {
    const { pngPath, warns, size } = await renderCover({ browser, spec, specDir, outDir, scale });
    console.log(`✓ ${path.relative(process.cwd(), pngPath)}  (${size} × ${size}px)`);
    warns.forEach((m) => console.log(`△ ${m}`));
    if (strict && warns.length) process.exit(1);
  } finally { await browser.close(); }
}
