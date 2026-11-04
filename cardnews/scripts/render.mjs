#!/usr/bin/env node
// HTML 카드뉴스를 PNG 로 캡처합니다.
//
//   node scripts/render.mjs decks/<deck>   # 한 덱
//   node scripts/render.mjs                # decks/ 아래 모든 덱
//
// 각 덱의 index.html 에서 .cn-card[data-name] 마다 out/<data-name>.png 를,
// 덱 전체를 한 장에 모은 out/overview.png 를 만듭니다.
// 카드는 Figma 1x(300 × 400)로 짜여 있고 SCALE(기본 3.6)배로 캡처해 1080 × 1440 이 됩니다.
//
// 환경 변수
//   SCALE=3.6                   출력 배율 (1080 / 300)
//   ALLOW_MISSING_IMAGES=1      사진이 없어도 자리 표시 색으로 렌더 (레이아웃 확인용)
//   STRICT=1                    글이 카드 밖으로 넘치거나 직접 나눈 줄보다 더 꺾이면 실패
//   CHROMIUM_PATH=/path/chrome  Playwright 기본 브라우저 대신 쓸 Chromium

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const SCALE = Number(process.env.SCALE || 3.6);
const allowMissing = process.env.ALLOW_MISSING_IMAGES === "1";
const strict = process.env.STRICT === "1";

let decks = process.argv.slice(2).map((d) => path.resolve(d));
if (decks.length === 0) {
  const base = path.join(ROOT, "decks");
  decks = (await fs.readdir(base, { withFileTypes: true }))
    .filter((d) => d.isDirectory())
    .map((d) => path.join(base, d.name));
}

const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
let failed = false;
try {
  for (const deck of decks) {
    const html = path.join(deck, "index.html");
    if (!(await fs.stat(html).catch(() => null))) continue;
    const out = path.join(deck, "out");
    await fs.rm(out, { recursive: true, force: true });
    await fs.mkdir(out, { recursive: true });

    const page = await browser.newPage({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: SCALE });
    await page.goto(pathToFileURL(html).href, { waitUntil: "load" });
    await page.evaluate(() => document.body.classList.add("cn-rendering"));
    await page.evaluate(() => document.fonts.ready);

    const fontOk = await page.evaluate(() => document.fonts.check('700 16px "Pretendard"'));
    if (!fontOk) throw new Error("Pretendard 폰트를 불러오지 못했습니다 (fonts/PretendardVariable.woff2 확인)");

    const missing = await page.$$eval(".cn-card img", (imgs) =>
      imgs.filter((i) => !i.complete || i.naturalWidth === 0).map((i) => i.getAttribute("src")));
    if (missing.length && !allowMissing) {
      throw new Error(`${path.relative(ROOT, deck)}: 사진이 없습니다 → ${missing.join(", ")}\n먼저 npm run fetch 를 실행하세요.`);
    }

    // 넘침 검사: 글이 카드 밖으로 나가거나 요소끼리 겹치면 경고
    const overflow = await page.$$eval(".cn-card", (cards) => cards.flatMap((card) => {
      const box = card.getBoundingClientRect();
      return [...card.querySelectorAll("*")]
        .filter((el) => !el.closest(".cn-photo, .cn-scrim"))
        .filter((el) => { const r = el.getBoundingClientRect(); return r.width && (r.bottom > box.bottom + 0.5 || r.right > box.right + 0.5); })
        .map((el) => `${card.dataset.name}: ${el.className || el.tagName}`);
    }));
    if (overflow.length) console.warn(`  ! 카드 밖으로 넘친 요소\n    ${overflow.join("\n    ")}`);

    // 줄 수 검사: 줄을 직접 나눈(<br>) 글이 칸이 좁아 한 줄 더 꺾였는지 확인합니다.
    let rewrapped = await page.$$eval(".cn-card", (cards) => cards.flatMap((card) => {
      const sel = ".cn-title, .cn-subtitle, .cn-eyebrow, .cn-point, .cn-pill, .cn-lead, .cn-desc, .cn-cell, .cn-bubble, " +
        ".cn-item-title, .cn-item-desc, .cn-row-title, .cn-row-desc, .cn-step-label, .cn-step-title, .cn-step-desc, " +
        ".cn-tile-title, .cn-kicker, .cn-checks li, .cn-note, .cn-sub";
      return [...card.querySelectorAll(sel)].flatMap((el) => {
        const range = document.createRange();
        range.selectNodeContents(el);
        const tops = new Set([...range.getClientRects()].filter((r) => r.width > 0).map((r) => Math.round(r.top)));
        const authored = el.querySelectorAll("br").length + 1;
        return tops.size > authored ? [`${card.dataset.name}: .${el.classList[0]} ${authored}줄 → ${tops.size}줄 "${el.textContent.trim().slice(0, 24)}"`] : [];
      });
    }));
    // 줄을 나누지 않는 문단은 최대 줄 수로 검사합니다 (본문 카드 문단 4줄, 타일 설명 2줄).
    const tooLong = await page.$$eval(".cn-card", (cards) => cards.flatMap((card) => {
      const MAX = { ".cn-story .cn-body": 4, ".cn-tile-desc": 2 };
      return Object.entries(MAX).flatMap(([sel, max]) => [...card.querySelectorAll(sel)].flatMap((el) => {
        const range = document.createRange();
        range.selectNodeContents(el);
        const n = new Set([...range.getClientRects()].filter((r) => r.width > 0).map((r) => Math.round(r.top))).size;
        return n > max ? [`${card.dataset.name}: ${sel} ${max}줄 이하여야 합니다 (지금 ${n}줄)`] : [];
      }));
    }));
    rewrapped.push(...tooLong);
    if (rewrapped.length) console.warn(`  ! 줄이 더 꺾인 글\n    ${rewrapped.join("\n    ")}`);
    if (strict && (overflow.length || rewrapped.length)) {
      throw new Error(`${path.relative(ROOT, deck)}: STRICT — 넘치거나 꺾인 글이 있습니다. deck.json 문구를 줄이세요.`);
    }

    const cards = await page.$$(".cn-card[data-name]");
    console.log(`\n▶ ${path.relative(ROOT, deck)} (${cards.length}장, ×${SCALE})`);
    for (const card of cards) {
      const name = await card.getAttribute("data-name");
      const file = path.join(out, `${name}.png`);
      await card.screenshot({ path: file, animations: "disabled" });
      console.log(`  ✓ out/${name}.png`);
    }

    // 한눈에 보기: 카드만 한 줄로 모아 1x 로 캡처
    const sheet = await browser.newPage({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 1.5 });
    await sheet.goto(pathToFileURL(html).href, { waitUntil: "load" });
    await sheet.evaluate(() => {
      document.body.classList.add("cn-rendering");
      document.querySelector("header")?.remove();
      const deckEl = document.querySelector(".cn-deck");
      deckEl.style.cssText = "flex-wrap:nowrap;gap:12px;padding:12px;width:max-content;background:#f5f5f5";
      deckEl.querySelectorAll("figcaption").forEach((c) => c.remove());
    });
    await sheet.evaluate(() => document.fonts.ready);
    await (await sheet.$(".cn-deck")).screenshot({ path: path.join(out, "overview.png") });
    console.log("  ✓ out/overview.png");
    await sheet.close();
    await page.close();
  }
} catch (err) {
  failed = true;
  console.error(`\n✗ ${err.message}`);
} finally {
  await browser.close();
}
process.exit(failed ? 1 : 0);
