#!/usr/bin/env node
// deck.json → index.html + images.json + caption.txt (인스타그램 문구)
//
//   node scripts/build-deck.mjs decks/<slug>            # 검증 후 생성
//   node scripts/build-deck.mjs decks/<slug> --check    # 검증만 (파일을 쓰지 않음)
//
// deck.json 형식과 템플릿별 필드는 cardnews/COPY_GUIDE.md 를 보세요.
// 문자열 안 표기:  *강조*  → 포인트색(.cn-hl), statement 제목에서는 형광펜(<em>)
//                 **굵게** → <strong> (grid 의 note)
// 여러 줄 필드는 문자열 배열이며 각 원소가 한 줄입니다.

import fs from "node:fs/promises";
import path from "node:path";

const args = process.argv.slice(2);
const checkOnly = args.includes("--check");
const deckDir = args.find((a) => !a.startsWith("--"));
if (!deckDir) {
  console.error("사용법: node scripts/build-deck.mjs decks/<slug> [--check]");
  process.exit(2);
}
const dir = path.resolve(deckDir);
const deck = JSON.parse(await fs.readFile(path.join(dir, "deck.json"), "utf8"));

// ---------------------------------------------------------------- text helpers

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const inline = (s, hl = "span") =>
  esc(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, hl === "em" ? "<em>$1</em>" : '<span class="cn-hl">$1</span>');
const lines = (v, hl) => (Array.isArray(v) ? v : [v]).map((l) => inline(l, hl)).join("<br>");
const plain = (s) => String(s).replace(/\*/g, "");
const asArray = (v) => (Array.isArray(v) ? v : [v]);

// ---------------------------------------------------------------- validation

// 줄 폭 검사: Pretendard 실측 글자 폭(em)으로 한 줄 길이를 계산해, 칸 너비(px) / 글자 크기(px)와 비교합니다.
// 한글 0.864em, 공백 0.24em, 영문 소문자 0.53em, 대문자 0.67em, 숫자 0.61em, 문장부호 0.34em.
function em(text, letterSpacing = 0) {
  let w = 0;
  for (const ch of plain(text)) {
    if (/[\uac00-\ud7a3\u3131-\u318e]/.test(ch)) w += 0.864;
    else if (ch === " ") w += 0.24;
    else if (/[a-z]/.test(ch)) w += 0.53;
    else if (/[A-Z]/.test(ch)) w += 0.67;
    else if (/[0-9]/.test(ch)) w += 0.61;
    else if (/[.,·:;!?'"()\-\/]/.test(ch)) w += 0.34;
    else w += 0.8;
    w += letterSpacing;
  }
  return w;
}
// 칸별 [사용 가능한 너비 px, 글자 크기 px, 자간 em] — cardnews.css 의 여백에서 계산
const BOX = {
  coverTitle: [234, 24], coverSub: [234, 14], pill: [150, 10],
  introTitle: [260, 24], introLabel: [260, 12],
  featureTitle: [252, 20], featureDesc: [252, 14],
  storyTitle: [232, 16], storyBody: [232 * 4, 12],
  checkTitle: [208, 16], checkItem: [208, 14], checkDesc: [191, 8],
  faqTitle: [252, 16], bubble: [159, 10],
  closingLead: [252, 15], closingTitle: [252, 20],
  headTitle: [244, 20], kicker: [244, 10, 0.08], sub: [244, 9],
  cell: [93, 11],
  rowTitle: [210, 13], rowDesc: [210, 9],
  splitCheck: [227, 11],
  tileTitle: [94, 13], tileDesc: [94 * 2, 9], note: [244, 9],
  stepLabel: [220, 10, 0.08], stepTitle: [220, 13], stepDesc: [220, 9],
  statementTitle: [244, 24], statementDesc: [244, 11],
};

const errors = [];
const where = (i, c, f) => `${String(i + 1).padStart(2, "0")} ${c.template}${f ? `.${f}` : ""}`;
function need(i, c, field) {
  const v = c[field];
  if (v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0)) {
    errors.push(`${where(i, c, field)}: 필수 항목이 없습니다`);
    return false;
  }
  return true;
}
function fit(i, c, field, value, box, maxLines = 99) {
  if (value === undefined) return;
  const [width, size, ls = 0] = BOX[box];
  const limit = (width / size) * 0.985; // 실측 폭 기준, 1.5% 여유
  const arr = asArray(value);
  if (arr.length > maxLines) errors.push(`${where(i, c, field)}: ${maxLines}줄 이하로 써 주세요 (지금 ${arr.length}줄)`);
  arr.forEach((l, n) => {
    const over = em(l, ls) - limit;
    if (over > 0) errors.push(`${where(i, c, field)}${arr.length > 1 ? `[${n + 1}]` : ""}: 칸보다 깁니다, 약 ${Math.ceil(over / 0.864)}자 줄이거나 줄을 나눠 주세요 "${plain(l)}"`);
  });
}
function count(i, c, field, min, max) {
  const n = (c[field] || []).length;
  if (n < min || n > max) errors.push(`${where(i, c, field)}: ${min === max ? `${min}개` : `${min}–${max}개`}여야 합니다 (지금 ${n}개)`);
}
const photoFiles = new Map(); // 사진 파일 이름 → 처음 쓴 카드
function photo(i, c) {
  if (!need(i, c, "photo")) return;
  if (!c.photo.alt) errors.push(`${where(i, c, "photo.alt")}: 사진 설명(alt)이 없습니다`);
  if (!c.photo.unsplash && !c.photo.query) errors.push(`${where(i, c, "photo")}: unsplash ID 나 query 중 하나는 있어야 합니다`);
  // 파일 이름은 images/ 안의 단순한 이름만 허용합니다 (경로 이동·덮어쓰기 방지).
  const file = c.photo.file || `${c.name}.jpg`;
  if (!/^[a-z0-9][a-z0-9-]*\.(jpg|jpeg|png)$/.test(file)) {
    errors.push(`${where(i, c, "photo.file")}: 영문 소문자·숫자·하이픈 이름에 .jpg/.png 확장자만 쓸 수 있습니다 ("${file}")`);
  } else if (photoFiles.has(file)) {
    errors.push(`${where(i, c, "photo.file")}: ${photoFiles.get(file)} 카드와 사진 파일 이름(${file})이 겹칩니다`);
  } else {
    photoFiles.set(file, String(i + 1).padStart(2, "0"));
  }
}
// 목록 항목마다 꼭 있어야 하는 필드. 빠지면 카드에 "undefined" 가 찍히므로 검사합니다.
const ITEM_FIELDS = {
  "cn-checklist": ["items", ["title", "desc"]],
  "cn-compare": ["rows", ["before", "after"]],
  "cn-summary": ["rows", ["title", "desc"]],
  "cn-split": ["checks", null],
  "cn-grid": ["tiles", ["title", "desc"]],
  "cn-steps": ["steps", ["title", "desc"]],
};
const blank = (v) => v === undefined || v === null || (Array.isArray(v) ? v.length === 0 || v.some(blank) : String(v).trim() === "");
function items(i, c) {
  const spec = ITEM_FIELDS[c.template];
  if (!spec || !Array.isArray(c[spec[0]])) return;
  const [list, keys] = spec;
  c[list].forEach((it, n) => {
    if (keys === null) {
      if (blank(it)) errors.push(`${where(i, c, `${list}[${n + 1}]`)}: 내용이 비어 있습니다`);
      return;
    }
    if (typeof it !== "object" || it === null) { errors.push(`${where(i, c, `${list}[${n + 1}]`)}: { ${keys.join(", ")} } 형태여야 합니다`); return; }
    for (const k of keys) if (blank(it[k])) errors.push(`${where(i, c, `${list}[${n + 1}].${k}`)}: 필수 항목이 없습니다`);
  });
}

const RULES = {
  "cn-cover": (i, c) => { photo(i, c); need(i, c, "pill"); need(i, c, "title"); need(i, c, "subtitle"); fit(i, c, "pill", c.pill, "pill", 1); fit(i, c, "title", c.title, "coverTitle", 2); fit(i, c, "subtitle", c.subtitle, "coverSub", 1); },
  "cn-intro": (i, c) => { photo(i, c); need(i, c, "eyebrow"); need(i, c, "title"); need(i, c, "point"); fit(i, c, "eyebrow", c.eyebrow, "introLabel", 1); fit(i, c, "title", c.title, "introTitle", 2); fit(i, c, "point", c.point, "introLabel", 1); },
  "cn-feature": (i, c) => { photo(i, c); need(i, c, "title"); need(i, c, "desc"); fit(i, c, "kicker", c.kicker, "kicker", 1); fit(i, c, "title", c.title, "featureTitle", 2); fit(i, c, "desc", c.desc, "featureDesc", 2); },
  "cn-story": (i, c) => { photo(i, c); need(i, c, "eyebrow"); need(i, c, "title"); need(i, c, "body"); fit(i, c, "title", c.title, "storyTitle", 1); fit(i, c, "body", c.body, "storyBody", 1); },
  "cn-checklist": (i, c) => {
    need(i, c, "title"); fit(i, c, "title", c.title, "checkTitle", 1); count(i, c, "items", 3, 3);
    (c.items || []).forEach((it, n) => { fit(i, c, `items[${n + 1}].title`, (it.num ? it.num + " " : "") + it.title, "checkItem", 1); fit(i, c, `items[${n + 1}].desc`, it.desc, "checkDesc", 2); });
  },
  "cn-faq": (i, c) => { photo(i, c); need(i, c, "title"); need(i, c, "question"); need(i, c, "answer"); fit(i, c, "title", c.title, "faqTitle", 2); fit(i, c, "question", c.question, "bubble", 2); fit(i, c, "answer", c.answer, "bubble", 2); },
  "cn-closing": (i, c) => { photo(i, c); need(i, c, "lead"); need(i, c, "title"); fit(i, c, "lead", c.lead, "closingLead", 2); fit(i, c, "title", c.title, "closingTitle", 1); },
  "cn-compare": (i, c) => {
    need(i, c, "title"); fit(i, c, "kicker", c.kicker, "kicker", 1); fit(i, c, "title", c.title, "headTitle", 2); count(i, c, "rows", 2, 4);
    (c.rows || []).forEach((r, n) => { fit(i, c, `rows[${n + 1}].before`, r.before, "cell", 2); fit(i, c, `rows[${n + 1}].after`, r.after, "cell", 2); });
  },
  "cn-summary": (i, c) => {
    need(i, c, "title"); fit(i, c, "kicker", c.kicker, "kicker", 1); fit(i, c, "title", c.title, "headTitle", 2); count(i, c, "rows", 3, 5);
    (c.rows || []).forEach((r, n) => { fit(i, c, `rows[${n + 1}].title`, r.title, "rowTitle", 1); fit(i, c, `rows[${n + 1}].desc`, r.desc, "rowDesc", 1); });
  },
  "cn-split": (i, c) => {
    photo(i, c); need(i, c, "title"); fit(i, c, "kicker", c.kicker, "kicker", 1); fit(i, c, "title", c.title, "headTitle", 2); count(i, c, "checks", 2, 4);
    (c.checks || []).forEach((t, n) => fit(i, c, `checks[${n + 1}]`, t, "splitCheck", 1));
  },
  "cn-grid": (i, c) => {
    need(i, c, "title"); fit(i, c, "kicker", c.kicker, "kicker", 1); fit(i, c, "title", c.title, "headTitle", 2); count(i, c, "tiles", 4, 4);
    (c.tiles || []).forEach((t, n) => { fit(i, c, `tiles[${n + 1}].title`, t.title, "tileTitle", 1); fit(i, c, `tiles[${n + 1}].desc`, t.desc, "tileDesc", 1); });
    fit(i, c, "sub", c.sub, "sub", 1); fit(i, c, "note", c.note, "note", 1);
  },
  "cn-steps": (i, c) => {
    need(i, c, "title"); fit(i, c, "kicker", c.kicker, "kicker", 1); fit(i, c, "title", c.title, "headTitle", 2); count(i, c, "steps", 3, 4);
    (c.steps || []).forEach((s, n) => { fit(i, c, `steps[${n + 1}].label`, s.label, "stepLabel", 1); fit(i, c, `steps[${n + 1}].title`, s.title, "stepTitle", 1); fit(i, c, `steps[${n + 1}].desc`, s.desc, "stepDesc", 1); });
  },
  "cn-statement": (i, c) => { need(i, c, "title"); fit(i, c, "title", c.title, "statementTitle", 3); fit(i, c, "desc", c.desc, "statementDesc", 2); },
};

if (!Array.isArray(deck.cards) || deck.cards.length < 7) errors.push(`cards: 7장 이상이어야 합니다 (지금 ${deck.cards?.length ?? 0}장)`);
if (deck.cards?.length > 20) errors.push(`cards: 20장 이하여야 합니다 (인스타그램 캐러셀 한도)`);

// 인스타그램 문구: caption.body(줄 배열) + caption.hashtags(태그 배열) → caption.txt
const EMOJI = /[\p{Extended_Pictographic}\u{1F1E6}-\u{1F1FF}]/u;
function captionText(cap) {
  const body = asArray(cap.body || []).join("\n").trim();
  const tags = (cap.hashtags || []).map((t) => `#${t}`).join(" ");
  return tags ? `${body}\n\n${tags}\n` : `${body}\n`;
}
if (!deck.caption || blankCaption(deck.caption.body)) {
  errors.push("caption.body: 인스타그램 문구가 없습니다 (COPY_GUIDE §7)");
} else {
  const tags = deck.caption.hashtags || [];
  if (!Array.isArray(tags)) errors.push("caption.hashtags: 태그 배열이어야 합니다");
  else {
    if (tags.length > 30) errors.push(`caption.hashtags: 30개 이하여야 합니다 (인스타그램 한도, 지금 ${tags.length}개)`);
    tags.forEach((t, n) => {
      if (typeof t !== "string" || !/^[^\s#]+$/u.test(t)) errors.push(`caption.hashtags[${n + 1}]: '#' 없이 공백 없는 한 단어로 적어 주세요 ("${t}")`);
    });
    if (new Set(tags).size !== tags.length) errors.push("caption.hashtags: 겹치는 태그가 있습니다");
  }
  const text = captionText(deck.caption);
  if ([...text].length > 2200) errors.push(`caption: 2,200자 이하여야 합니다 (인스타그램 한도, 지금 ${[...text].length}자)`);
  if (EMOJI.test(text)) errors.push("caption: 이모지는 쓰지 않습니다 (브랜드 규칙)");
}
function blankCaption(v) { return !v || asArray(v).join("").trim() === ""; }
const cards = deck.cards || [];
if (cards[0] && cards[0].template !== "cn-cover") errors.push("첫 카드는 cn-cover 여야 합니다");
if (cards.length && cards.at(-1).template !== "cn-closing") errors.push("마지막 카드는 cn-closing 이어야 합니다");
const names = new Set();
cards.forEach((c, i) => {
  if (!RULES[c.template]) { errors.push(`${where(i, c)}: 알 수 없는 템플릿입니다 (${Object.keys(RULES).join(", ")})`); return; }
  if (i > 0 && cards[i - 1].template === c.template) errors.push(`${where(i, c)}: 같은 템플릿을 연달아 쓰지 마세요`);
  if (!c.name || !/^[a-z0-9-]+$/.test(c.name)) errors.push(`${where(i, c, "name")}: 영문 소문자·숫자·하이픈 이름이 필요합니다`);
  if (names.has(c.name)) errors.push(`${where(i, c, "name")}: 이름이 겹칩니다`);
  names.add(c.name);
  RULES[c.template](i, c);
  items(i, c);
});

if (errors.length) {
  console.error(`✗ ${path.relative(process.cwd(), dir)}/deck.json — ${errors.length}개 문제\n  ${errors.join("\n  ")}`);
  process.exit(1);
}
if (checkOnly) {
  console.log(`✓ ${path.relative(process.cwd(), dir)}/deck.json — ${cards.length}장, 문제 없음`);
  process.exit(0);
}

// ---------------------------------------------------------------- render

const LABEL = {
  "cn-cover": "표지", "cn-intro": "도입", "cn-feature": "포인트", "cn-story": "본문", "cn-checklist": "리스트",
  "cn-faq": "FAQ", "cn-closing": "마무리", "cn-compare": "비교", "cn-summary": "요약", "cn-split": "사진 + 체크",
  "cn-grid": "타일", "cn-steps": "단계", "cn-statement": "핵심 메시지",
};
const dataName = (i, c) => `${String(i + 1).padStart(2, "0")}-${c.name}`;
const photoFile = (c) => c.photo.file || `${c.name}.jpg`;
const img = (c) => `<img src="images/${esc(photoFile(c))}" alt="${esc(c.photo.alt)}"${c.photo.position ? ` style="object-position: ${esc(c.photo.position)}"` : ""}>`;
const head = (c, I) => [
  `${I}<div class="cn-head">`,
  c.kicker ? `${I}  <p class="cn-kicker">${inline(c.kicker)}</p>` : null,
  `${I}  <h2 class="cn-title">${lines(c.title)}</h2>`,
  c.sub ? `${I}  <p class="cn-sub">${inline(c.sub)}</p>` : null,
  `${I}</div>`,
];

const T = {
  "cn-cover": (c) => [
    `<div class="cn-photo">${img(c)}</div>`,
    `<div class="cn-scrim cn-scrim--bottom"></div>`,
    `<div class="cn-content">`,
    `  <span class="cn-pill">${inline(c.pill)}</span>`,
    `  <h2 class="cn-title">${lines(c.title)}</h2>`,
    `  <p class="cn-subtitle">${inline(c.subtitle)}</p>`,
    `</div>`,
  ],
  "cn-intro": (c) => [
    `<div class="cn-photo">${img(c)}</div>`,
    `<div class="cn-scrim cn-scrim--top"></div>`,
    `<div class="cn-content">`,
    `  <p class="cn-eyebrow">${inline(c.eyebrow)}</p>`,
    `  <h2 class="cn-title">${lines(c.title)}</h2>`,
    `  <p class="cn-point">${inline(c.point)}</p>`,
    `</div>`,
  ],
  "cn-feature": (c) => [
    `<div class="cn-content">`,
    `  <div class="cn-image">${img(c)}</div>`,
    c.kicker ? `  <p class="cn-kicker">${inline(c.kicker)}</p>` : null,
    `  <h2 class="cn-title">${lines(c.title)}</h2>`,
    `  <p class="cn-desc">${lines(c.desc)}</p>`,
    `</div>`,
  ],
  "cn-story": (c) => [
    `<div class="cn-content">`,
    `  <p class="cn-eyebrow">${inline(c.eyebrow)}</p>`,
    `  <h2 class="cn-title">${inline(c.title)}</h2>`,
    `  <div class="cn-image">${img(c)}</div>`,
    `  <p class="cn-body">${inline(c.body)}</p>`,
    `</div>`,
  ],
  "cn-checklist": (c) => [
    `<div class="cn-content">`,
    `  <h2 class="cn-title">${inline(c.title)}</h2>`,
    `  <ul class="cn-list">`,
    ...c.items.flatMap((it) => [
      `    <li>`,
      `      <p class="cn-item-title">${it.num ? `<span class="cn-num">${esc(it.num)}</span>` : ""}${inline(it.title)}</p>`,
      `      <p class="cn-item-desc">${lines(it.desc)}</p>`,
      `    </li>`,
    ]),
    `  </ul>`,
    `</div>`,
  ],
  "cn-faq": (c) => [
    `<div class="cn-content">`,
    `  <h2 class="cn-title">${lines(c.title)}</h2>`,
    `  <p class="cn-bubble cn-bubble--q">${lines(c.question)}</p>`,
    `  <div class="cn-image">${img(c)}</div>`,
    `  <p class="cn-bubble cn-bubble--a">${lines(c.answer)}</p>`,
    `</div>`,
  ],
  "cn-closing": (c) => [
    `<div class="cn-photo">${img(c)}</div>`,
    `<div class="cn-scrim cn-scrim--flat"></div>`,
    `<div class="cn-content">`,
    `  <p class="cn-lead">${lines(c.lead)}</p>`,
    `  <h2 class="cn-title">${inline(c.title)}</h2>`,
    `</div>`,
  ],
  "cn-compare": (c) => [
    ...head(c, ""),
    `<div class="cn-table">`,
    `  <p class="cn-col-head cn-col-head--before">${inline(c.before_label || "이전")}</p><span></span><p class="cn-col-head cn-col-head--after">${inline(c.after_label || "지금")}</p>`,
    ...c.rows.map((r) => `  <p class="cn-cell cn-cell--before">${lines(r.before)}</p><span class="cn-arrow"></span><p class="cn-cell cn-cell--after">${lines(r.after)}</p>`),
    `</div>`,
  ],
  "cn-summary": (c) => [
    ...head(c, ""),
    `<ol class="cn-rows">`,
    ...c.rows.map((r, n) => `  <li class="cn-row"><span class="cn-badge">${esc(r.num || String(n + 1).padStart(2, "0"))}</span><div><p class="cn-row-title">${inline(r.title)}</p><p class="cn-row-desc">${inline(r.desc)}</p></div></li>`),
    `</ol>`,
  ],
  "cn-split": (c) => [
    `<div class="cn-image">${img(c)}</div>`,
    `<div class="cn-body">`,
    c.kicker ? `  <p class="cn-kicker">${inline(c.kicker)}</p>` : null,
    `  <h2 class="cn-title">${lines(c.title)}</h2>`,
    `  <ul class="cn-checks">`,
    ...c.checks.map((t) => `    <li>${inline(t)}</li>`),
    `  </ul>`,
    `</div>`,
  ],
  "cn-grid": (c) => [
    ...head(c, ""),
    `<div class="cn-tiles">`,
    ...c.tiles.map((t, n) => `  <div class="cn-tile${t.point ? " is-point" : ""}"><p class="cn-tile-num">${esc(t.num || n + 1)}</p><p class="cn-tile-title">${inline(t.title)}</p><p class="cn-tile-desc">${inline(t.desc)}</p></div>`),
    `</div>`,
    c.note ? `<p class="cn-note">${inline(c.note)}</p>` : null,
  ],
  "cn-steps": (c) => [
    ...head(c, ""),
    `<ol class="cn-timeline">`,
    ...c.steps.map((s, n) => `  <li class="cn-step${s.point ? " is-point" : ""}"><p class="cn-step-label">${inline(s.label || `STEP ${n + 1}`)}</p><p class="cn-step-title">${inline(s.title)}</p><p class="cn-step-desc">${inline(s.desc)}</p></li>`),
    `</ol>`,
  ],
  "cn-statement": (c) => [
    `<div class="cn-content">`,
    `  <span class="cn-mark"></span>`,
    `  <p class="cn-kicker">${inline(c.kicker || "KEY MESSAGE")}</p>`,
    `  <h2 class="cn-title">${lines(c.title, "em")}</h2>`,
    c.desc ? `  <p class="cn-desc">${lines(c.desc)}</p>` : null,
    `</div>`,
    `<p class="cn-foot">${inline(c.foot || "INSIGHT LEARNING")}</p>`,
  ],
};
const DARK = new Set(["cn-cover", "cn-intro", "cn-closing"]);

const sections = cards.map((c, i) => {
  const body = T[c.template](c).filter((l) => l !== null).map((l) => `      ${l}`);
  return [
    `    <!-- ${String(i + 1).padStart(2, "0")} ${c.label || LABEL[c.template]} -->`,
    `    <section class="cn-card ${c.template}${DARK.has(c.template) ? " cn-on-dark" : ""}" data-name="${dataName(i, c)}">`,
    ...body,
    `    </section>`,
  ].join("\n");
});

const html = `<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${esc(deck.title)} — 카드뉴스</title>
  <link rel="stylesheet" href="../../cardnews.css">
</head>
<body class="cn-preview">
  <header>
    <h1>${esc(deck.title)}</h1>
    <p>카드 ${cards.length}장 · 1080 × 1440 PNG 는 out/ 폴더 · 사진 출처는 CREDITS.md</p>
  </header>

  <main class="cn-deck">

${sections.join("\n\n")}

  </main>
  <script>
    // 사진을 아직 받지 않았으면(npm run fetch 전) 깨진 아이콘 대신 자리 표시 색만 보이게 합니다.
    document.querySelectorAll('.cn-card img').forEach(function (img) {
      img.addEventListener('error', function () { img.style.visibility = 'hidden'; img.dataset.missing = '1'; });
    });
  </script>
</body>
</html>
`;

// images.json: 이미 받은 사진의 사진가 정보는 같은 ID 일 때 유지합니다.
const manifestPath = path.join(dir, "images.json");
let previous = { width: 1600, images: [] };
try { previous = JSON.parse(await fs.readFile(manifestPath, "utf8")); } catch { /* 새 덱 */ }
const byFile = new Map(previous.images.map((p) => [p.file, p]));
const images = cards.filter((c) => c.photo).map((c) => {
  const file = photoFile(c);
  const prev = byFile.get(file);
  // ID 없이 query 만 준 사진은 fetch-images.mjs 가 검색으로 고른 ID 를 그대로 이어 씁니다.
  const picked = !c.photo.unsplash && prev && prev.query === (c.photo.query || "") ? prev.unsplash || "" : "";
  const id = c.photo.unsplash || picked;
  const same = prev && prev.unsplash && prev.unsplash === id;
  const entry = { file, card: dataName(cards.indexOf(c), c), query: c.photo.query || "", unsplash: id };
  const page = c.photo.page || (picked && prev.page) || (id ? `https://unsplash.com/photos/${id}` : undefined);
  if (page) entry.page = page;
  if (same && prev.author) entry.author = prev.author;
  if (same && prev.author_url) entry.author_url = prev.author_url;
  return entry;
});
// 같은 ID 가 바뀌었으면 이전에 받은 사진 파일을 지워 다시 받게 합니다.
for (const e of images) {
  const prev = byFile.get(e.file);
  if (prev && prev.unsplash !== e.unsplash) await fs.rm(path.join(dir, "images", e.file), { force: true });
}

await fs.writeFile(path.join(dir, "index.html"), html);
await fs.writeFile(path.join(dir, "caption.txt"), captionText(deck.caption));
await fs.writeFile(manifestPath, JSON.stringify({ width: previous.width || 1600, images }, null, 2) + "\n");
console.log(`✓ ${path.relative(process.cwd(), dir)} — 카드 ${cards.length}장, 사진 ${images.length}장 → index.html, images.json, caption.txt`);
