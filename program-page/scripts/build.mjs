#!/usr/bin/env node
// 교육 프로그램 상세페이지: page.json → index.html → PNG
//
//   node program-page/scripts/build.mjs <page.json> [옵션]
//
// 옵션
//   --check           구조만 검사 (렌더 안 함)
//   --scale <n>       출력 배율 (기본 2 → 1380px 폭)
//   --out <dir>       결과 폴더 (기본: page.json 이 있는 폴더)
//   --strict          줄 꺾임·이미지 누락 경고도 실패로 처리
//
// 결과: <out>/index.html, <out>/<name>.png (name 이 없으면 page)
//       cover 가 있으면 <out>/<name>_표지.png (1:1, scripts/cover.mjs)
// 스키마와 섹션 고르는 법: program-page/README.md, .claude/skills/program-page/references/section-guide.md

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";
import { renderCover } from "./cover.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PP = path.resolve(HERE, "..");
const ROOT = path.resolve(PP, "..");
const ICONS = path.join(ROOT, "assets", "icons", "tabler-outline");
const FONT = path.join(ROOT, "fonts", "PretendardVariable.woff2");

// ── 인자 ────────────────────────────────────────────
const args = process.argv.slice(2);
const opt = { check: false, strict: false, scale: 2, out: null };
let specPath = null;
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === "--check") opt.check = true;
  else if (a === "--strict") opt.strict = true;
  else if (a === "--scale") opt.scale = Number(args[++i]);
  else if (a === "--out") opt.out = args[++i];
  else if (!specPath) specPath = a;
  else die(`알 수 없는 인자: ${a}`);
}
if (!specPath) die("사용법: node program-page/scripts/build.mjs <page.json> [--check] [--scale 2] [--out dir] [--strict]");
specPath = path.resolve(specPath);
const specDir = path.dirname(specPath);
const outDir = path.resolve(opt.out || specDir);

function die(msg) { console.error(`✗ ${msg}`); process.exit(1); }

const spec = JSON.parse(await fs.readFile(specPath, "utf8"));

// ── 구조 검사 ───────────────────────────────────────
const SECTION_TYPES = ["checks", "bullets", "modules", "quotes", "images"];
const errors = [];
const warns = [];
const E = (m) => errors.push(m);
const W = (m) => warns.push(m);
const isStr = (v) => typeof v === "string" && v.trim().length > 0;
const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F000}-\u{1F2FF}]/u;

function textOf(v) { return typeof v === "string" ? v : ""; }
function walkStrings(o, f, at = "") {
  if (typeof o === "string") f(o, at);
  else if (Array.isArray(o)) o.forEach((x, i) => walkStrings(x, f, `${at}[${i}]`));
  else if (o && typeof o === "object") for (const [k, v] of Object.entries(o)) walkStrings(v, f, at ? `${at}.${k}` : k);
}

if (!isStr(spec.category)) E("category(영문 카테고리)가 비어 있습니다");
else if (spec.category !== spec.category.toUpperCase()) W(`category 는 대문자로 씁니다: ${spec.category}`);
if (!isStr(spec.title)) E("title(과정명)이 비어 있습니다");
if (!Array.isArray(spec.info) || spec.info.length < 1 || spec.info.length > 3) E("info 는 1–3칸입니다 (보통 2칸: 대상/키워드 + 교육 시간)");
else spec.info.forEach((p, i) => {
  if (!isStr(p.label) || !isStr(p.value)) E(`info[${i}]: label 과 value 가 필요합니다`);
  if (p.icon && !/^[a-z0-9-]+$/.test(p.icon)) E(`info[${i}].icon: tabler 아이콘 이름만 씁니다 (예 user, clock, check)`);
});
if (!Array.isArray(spec.sections) || spec.sections.length < 1) E("sections 가 비어 있습니다");
else spec.sections.forEach((s, i) => {
  const at = `sections[${i}]`;
  if (!SECTION_TYPES.includes(s.type)) return E(`${at}.type 은 ${SECTION_TYPES.join(" | ")} 중 하나입니다`);
  if (!isStr(s.en) || !isStr(s.title)) E(`${at}: en(영문 라벨)과 title(한글 제목)이 필요합니다`);
  if (!Array.isArray(s.items) || s.items.length === 0) return E(`${at}.items 가 비어 있습니다`);
  const n = s.items.length;
  if (s.type === "checks" && (n < 2 || n > 6)) W(`${at}: 체크 항목은 3–5개가 적당합니다 (지금 ${n}개)`);
  if (s.type === "bullets" && n > 9) W(`${at}: 점 목록이 ${n}개입니다 — 9개 이하로 묶어 주세요`);
  if (s.type === "modules") {
    if (n > 8) W(`${at}: 모듈이 ${n}개입니다 — 8개 이하로 묶어 주세요`);
    s.items.forEach((m, j) => { if (!isStr(m.title)) E(`${at}.items[${j}].title 이 비어 있습니다`); });
    if (s.numbering && !["M", "01", "1"].includes(s.numbering)) E(`${at}.numbering 은 "M" | "01" | "1" 중 하나이거나 생략합니다`);
  }
  if (s.type === "quotes") s.items.forEach((q, j) => { if (!isStr(q.quote)) E(`${at}.items[${j}].quote 가 비어 있습니다`); });
});
walkStrings(spec, (s, at) => {
  if (EMOJI.test(s)) E(`${at}: 이모지는 쓰지 않습니다`);
  if (s.includes("**") && !at.includes(".quote")) W(`${at}: ** 강조는 후기 인용(quote)에서만 색이 바뀝니다 — 다른 곳에서는 지웁니다`);
});

if (errors.length) {
  errors.forEach((m) => console.error(`✗ ${m}`));
  warns.forEach((m) => console.error(`△ ${m}`));
  process.exit(1);
}
if (opt.check) {
  warns.forEach((m) => console.log(`△ ${m}`));
  console.log(`✓ 구조 검사 통과: ${path.relative(process.cwd(), specPath)}`);
  process.exit(0);
}

// ── HTML ───────────────────────────────────────────
const esc = (s) => textOf(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const plain = (s) => esc(textOf(s).replace(/\*\*/g, "")).replace(/\n/g, "<br>");
const emph = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<em>$1</em>").replace(/\n/g, "<br>");

async function icon(name) {
  try {
    const raw = await fs.readFile(path.join(ICONS, `${name}.svg`), "utf8");
    return raw.replace(/<!--[\s\S]*?-->/g, "").replace(/\s+width="24"\s+height="24"/, "").trim();
  } catch {
    W(`아이콘 ${name}.svg 를 찾지 못했습니다 — 아이콘 없이 렌더합니다`);
    return "<span></span>";
  }
}
const CHECK = `<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="8" fill="#00317d"/><path d="M4.6 8.2l2.3 2.3 4.6-4.7" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const QMARK = `<svg class="qm" viewBox="0 0 16 12" fill="currentColor" aria-hidden="true"><path d="M0 12V7.2C0 3.6 1.9 1.1 5.6 0l.7 1.5C4.3 2.3 3.3 3.6 3.2 5.4H6.6V12H0Zm9.4 0V7.2C9.4 3.6 11.3 1.1 15 0l.7 1.5c-2 .8-3 2.1-3.1 3.9H16V12H9.4Z"/></svg>`;

const missingImages = [];
function img(src, cls = "", where = "") {
  if (!isStr(src)) { missingImages.push(where); return `<div class="ph missing ${cls}">이미지</div>`; }
  const abs = path.resolve(specDir, src);
  return `<div class="ph ${cls}"><img src="${pathToFileURL(abs).href}" data-src="${esc(src)}" alt=""></div>`;
}

function code(numbering, i) {
  if (numbering === "M") return `M${i + 1}`;
  if (numbering === "01") return `${String(i + 1).padStart(2, "0")}.`;
  if (numbering === "1") return `${i + 1}.`;
  return "";
}

async function section(s) {
  const head = `<div class="pp-en">${esc(s.en)}</div><h2 class="pp-h2">${esc(s.title)}</h2>`;
  let body = "";
  if (s.type === "checks") {
    body = `<ul class="pp-checks">${s.items.map((t) => `<li data-line="check">${CHECK}<span class="t">${plain(t)}</span></li>`).join("")}</ul>`;
  } else if (s.type === "bullets") {
    body = `<div class="pp-box"><ul class="pp-bullets">${s.items.map((t) => `<li data-line="bullet">${plain(t)}</li>`).join("")}</ul></div>`;
  } else if (s.type === "modules") {
    body = `<div class="pp-box"><ul class="pp-modules">${s.items.map((m, i) => {
      const c = m.code ?? code(s.numbering, i);
      return `<li><div class="mt" data-line="module-title">${c ? `<span class="code${c.endsWith(".") ? " dot" : ""}">${esc(c)}</span>` : ""}${plain(m.title)}</div>${
        isStr(m.desc) ? `<div class="md" data-line="module-desc">${plain(m.desc)}</div>` : ""}</li>`;
    }).join("")}</ul></div>`;
  } else if (s.type === "quotes") {
    const cols = s.columns || Math.min(4, s.items.length);
    body = `<div class="pp-quotes" style="--cols:${cols}">${s.items.map((q) =>
      `<div class="pp-quote">${QMARK}<div class="qt">${emph(q.quote)}</div>${img(q.image, "", `${s.title} ${s.items.indexOf(q) + 1}`)}${isStr(q.caption) ? `<div class="cap">${plain(q.caption)}</div>` : ""}</div>`).join("")}</div>`;
  } else if (s.type === "images") {
    const cols = s.columns || Math.min(3, s.items.length);
    const ratio = s.ratio || "3 / 4";
    body = `<div class="pp-images" style="--cols:${cols};--ratio:${esc(ratio)}">${s.items.map((q) => {
      const ph = img(q.image, q.fit === "cover" ? "" : "contain", `${s.title} ${s.items.indexOf(q) + 1}`).replace(/<\/div>$/, q.sample ? `<span class="stamp">SAMPLE</span></div>` : "</div>");
      return `<div class="pp-img">${ph}${isStr(q.caption) ? `<div class="cap">${plain(q.caption)}</div>` : ""}</div>`;
    }).join("")}</div>`;
  }
  return `<section class="pp-sec">${head}${body}</section>`;
}

const pills = [];
for (const p of spec.info) {
  pills.push(`<div class="pp-pill" data-line="pill">${p.icon ? await icon(p.icon) : "<span></span>"}<span class="lab">${esc(p.label)}</span><span class="bar"></span><span class="val">${plain(p.value)}</span></div>`);
}
const sections = [];
for (const s of spec.sections) sections.push(await section(s));

const css = (await fs.readFile(path.join(PP, "page.css"), "utf8")).replaceAll("__FONT_URL__", pathToFileURL(FONT).href);
const html = `<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>${esc(spec.title)}</title>
<style>${css}</style></head>
<body><main class="pp" id="page">
<header class="pp-head"><div class="pp-eyebrow">${esc(spec.category)}</div><h1 class="pp-title" data-line="title">${plain(spec.title)}</h1></header>
<div class="pp-info">${pills.join("")}</div>
<hr class="pp-rule">
${sections.join("\n")}
</main></body></html>`;

await fs.mkdir(outDir, { recursive: true });
const htmlPath = path.join(outDir, "index.html");
await fs.writeFile(htmlPath, html);

// ── 렌더 + 레이아웃 검사 ───────────────────────────
const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); }
catch { die("playwright 를 찾지 못했습니다. cd program-page && npm install (또는 NODE_PATH 에 전역 node_modules 지정)"); }

const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const name = (spec.name || "page").replace(/[\\/:*?"<>|]/g, "_");
const pngPath = path.join(outDir, `${name}.png`);
try {
  const page = await browser.newPage({ viewport: { width: 690, height: 900 }, deviceScaleFactor: opt.scale });
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  if (!(await page.evaluate(() => document.fonts.check('700 16px "Pretendard"')))) die("Pretendard 폰트를 불러오지 못했습니다 (fonts/PretendardVariable.woff2)");

  const report = await page.evaluate(() => {
    const out = { wraps: [], overflow: [], broken: [] };
    const lines = (el) => {
      const r = document.createRange(); r.selectNodeContents(el);
      const tops = new Set([...r.getClientRects()].filter((x) => x.width > 1).map((x) => Math.round(x.top)));
      return tops.size;
    };
    document.querySelectorAll("[data-line]").forEach((el) => {
      const kind = el.dataset.line;
      const target = el.querySelector(".t, .val") || el;
      const n = lines(target);
      if (kind === "title" && n > 2) out.wraps.push({ kind, n, text: target.textContent.trim() });
      const limit = (kind === "title" ? 2 : 1) + target.querySelectorAll("br").length;
      if (n > limit && kind !== "title") out.wraps.push({ kind, n, text: target.textContent.trim() });
    });
    const W = document.getElementById("page").getBoundingClientRect().right;
    document.querySelectorAll(".pp *").forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.right > W + 0.5) out.overflow.push(el.className || el.tagName);
    });
    document.querySelectorAll("img").forEach((i) => { if (!i.complete || i.naturalWidth === 0) out.broken.push(i.dataset.src); });
    out.titleLines = lines(document.querySelector(".pp-title"));
    return out;
  });

  const KIND = { title: "과정명", check: "체크 항목", bullet: "점 목록", "module-title": "모듈 제목", "module-desc": "모듈 설명", pill: "정보칸" };
  for (const w of report.wraps) W(`[${KIND[w.kind] || w.kind}] ${w.n}줄로 꺾입니다 → 줄이거나 나누세요: "${w.text}"`);
  if (report.titleLines === 2 && !spec.title.includes("\n")) W("과정명이 2줄로 꺾였습니다 — 의미 단위로 끊으려면 title 에 \\n 을 넣으세요");
  if (report.overflow.length) W(`페이지 폭을 넘는 요소가 있습니다: ${[...new Set(report.overflow)].slice(0, 5).join(", ")}`);
  for (const b of report.broken) W(`이미지를 불러오지 못했습니다: ${b}`);
  if (missingImages.length) W(`이미지 ${missingImages.length}칸이 비어 회색 자리 표시로 렌더했습니다 (${missingImages.join(", ")}) — 납품 전에 채우거나 섹션을 빼세요`);

  const el = await page.$("#page");
  await el.screenshot({ path: pngPath });
  const box = await el.boundingBox();
  console.log(`✓ ${path.relative(process.cwd(), pngPath)}  (${Math.round(box.width * opt.scale)} × ${Math.round(box.height * opt.scale)}px)`);

  if (spec.cover) {
    const cv = await renderCover({ browser, spec, specDir, outDir, scale: opt.scale });
    console.log(`✓ ${path.relative(process.cwd(), cv.pngPath)}  (${cv.size} × ${cv.size}px)`);
    warns.push(...cv.warns);
  }
} finally {
  await browser.close();
}

warns.forEach((m) => console.log(`△ ${m}`));
if (opt.strict && warns.length) die(`--strict: 경고 ${warns.length}건`);
