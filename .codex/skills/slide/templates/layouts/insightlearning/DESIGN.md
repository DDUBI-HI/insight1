# DESIGN.md — Insightlearning

> Preset-level design vocabulary for `slide-plan` consumption.
> Pairs with `theme-active.json` (token SSOT) and `references/patterns.md` (HTML pattern catalog).
>
> **Purpose:** Give `slide-plan` the structured vocabulary it needs to produce `slide_plan.json` entries (`recommended_layout_family`, `chart_strategy`) that `/slide` Executor can consume without re-deciding visual style.
>
> **Scope:** Insightlearning only. Other presets supply their own `DESIGN.md` via `/theme-init`.
>
> **Source:** 인싸이트러닝 2026 회사소개서 디자인 가이드 (`README.md` + `tokens.json`, designed on a 1440×810 canvas). Every pixel value below is already scaled ×0.889 to the locked 1280×720 canvas.

---

## 1. Visual Theme & Atmosphere

- **Tone:** navy-first, square, quiet, consultative, evidence-led.
- **Moodboard:** a Korean HRD consulting company profile — McKinsey-style report pages softened by generous white, one deep navy (`#012281`) carrying every structural field, light filled cards, grayscale corporate photography.
- **Atmosphere:** the deck reads like 고객사's *external education-planning team* presenting a plan: calm, organised, every slide makes one claim and proves it with a real figure, a table or a process.
- **Anti-mood:** not a colourful SaaS dashboard, not a startup pitch with gradients and glows, not playful illustration. No shadows, no gradients, no rainbow charts, no emoji, no rounded "bubbly" panels on big navy fields.
- **Litmus test:** *"Would this slide sit naturally between the 'OUR SERVICE' and 'OUR EXPERIENCE' pages of the 인싸이트러닝 company profile?"* If it needs a second hue or a drop shadow to look finished, it is wrong.

**Voice anchors (from theme-active.json):**
- **Tone:** consultative, confident, polite declarative (~합니다 / ~하겠습니다), contrast-framed
- **Point of view:** first-person corporate — the company speaks as 인싸이트러닝 and calls the client 고객사
- **Register:** Korean HRD consulting proposal / company profile, English for programme names, frameworks and section titles

**House rhetoric:** contrast framing — "규모보다 깊이, 카탈로그보다 맞춤성, 강사 공급보다 해결 설계". Lists are noun phrases joined by ` · ` or ` / ` with no sentence punctuation ("리더십 · 코칭 · 워크숍"). Real figures only (2014 설립, 665개 프로그램, 648건 세션, 19,614명).

---

## 2. Palette & Contrast Behavior

### 2.1 Allowed colors (literal, locked)

This preset is navy + light neutrals. The ONLY hex values that may appear in any generated content SVG / CSS / chart palette are:

| Token | Hex | Role |
|---|---|---|
| `--bg` | `#FFFFFF` | page background |
| `--surface` | `#F8F8F8` | filled content card / stat card (guide: `surface-card`) |
| `--surface-alt` | `#F2F2F2` | card header band, tag, timeline tile (guide: `surface-alt` / `surface-tile`) |
| `--text` | `#000000` | headlines, display titles (guide: `ink`) |
| `--text-secondary` | `#595959` | body copy, GM line (guide: `ink-body`) |
| `--text-tertiary` | `#666666` | captions, key–value values, page numbers (guide: `ink-muted`) |
| `--border` | `#DFDFDF` | hairline dividers, table borders, chart gridlines (guide: `line`) |
| `--border-strong` | `#B2B2B2` | emphasis divider |
| `--accent` | `#012281` | Insight Navy — the brand. Panels, chevrons, table headers, primary bars, title rule |
| `--accent-soft` | `#E0EDF3` | the one highlighted card in a row (guide: `tint-sky`); label text on navy panels |
| `--accent-ink` | `#01185A` | navy pressed / second navy tier |
| `--positive` | `#059669` | data context only |
| `--negative` | `#E11D48` | data context only |
| `--warning` | `#D97706` | data context only |

**Narrative shells only** (cover / chapter / closing — Rule T9): `shell-bg #012281`, `shell-text #FFFFFF`, `shell-text-secondary #B3BDD9`, `shell-accent #58CCFF` (Insight Sky).

**Guide colours deliberately NOT carried into content slides** (single-accent lock): `sky #58CCFF` (only on navy narrative shells), `chart-blue #58A6F6` → use navy at `fill-opacity` 0.45 for a second series, `steel #486FB0` → use navy at `fill-opacity` 0.7 for table row headers, `ink-navy #1F375D` → use `--accent` for English card titles, `ink-strong #333333` → use `--text`.

### 2.2 Contrast & accent budget

- **Max 2 accent events per content slide** (Rule T2). An event = accent text, an accent-filled field (navy panel, navy table header, navy chevron row), or an accent-soft highlighted card. The shell's navy title rule is chrome and does not count.
- A **navy panel / navy header row counts as one event**, however large. Inside it, text is `#FFFFFF`; its labels use `--accent-soft` (`#E0EDF3`) — never sky on a content slide.
- **Card differentiation:** cards are `--surface` fills with no border. Exactly one card in a row may be lifted to `--accent-soft` (the "2026~ 프로젝트 확대" treatment). Never two.
- **Semantic colours** (`positive` / `negative` / `warning`) only when the colour encodes data meaning (growth vs decline). Never decorative, never for category labels.
- **Chart palette:** navy opacity ladder — primary series `#012281` at 1.0, second series at 0.45, further series at 0.25 / 0.12. Gridlines `--border`.
- **Contrast:** never set body text in a lighter value than `--text-tertiary`. Large numerals may be navy.

### 2.3 Background hierarchy

`bg #FFFFFF` (slide) → `surface #F8F8F8` (filled card) → `surface-alt #F2F2F2` (card header band / tag / tile inside a card) → `accent-soft #E0EDF3` (the single highlighted item) → `accent #012281` (navy field: panel, header row, chevron).

- Skipping from `bg` straight to `accent-soft` is allowed only for the single highlight card in a row.
- Never nest `surface` inside `surface`; use `surface-alt` for the inner tier.
- Navy fields sit directly on `bg`, never inside a card.

---

## 3. Typography Hierarchy

### 3.1 Font chain (locked)

```
Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif
```

Every `<text>` element in generated SVG uses this exact chain. (The guide's display face, Noto Sans KR Black, is approximated with Pretendard weight 900 — one font chain is a permanent lock.)

### 3.2 Type scale

| Role | Size (px) | Weight | LH | Tracking | Use |
|---|---|---|---|---|---|
| Display | 52 | 700 | 1.2 | -1.56 | title slide hero |
| Display-sm | 41 | 800 | 1.1 | -0.8 | hero stat / closing accent |
| Headline | 30 | 800 | 1.3 | -0.9 | content slide title |
| Title | 17 | 700 | 1.4 | -0.34 | card title, subtitle |
| Body | 15.2 | 400 | 1.65 | -0.3 | body text |
| Caption | 12.8 | 400 | 1.6 | 0.0 | annotations |
| Label | 12.8 | 600 | 1.3 | 0.26 | uppercase taxonomy (eyebrow) |

Shell-only literals (from the guide, scaled): slide label 22 / 300 (top-left); section-opener English title 56 / 900 uppercase; section number 48 / 300; cover eyebrow 18 / 400, tracking 7 (0.4em).

### 3.3 Hierarchy rules

- **Per content slide:** slide label (top-left, Light, shell) → headline (ExtraBold, centered, shell) → optional lead sentence (body 15.2, `--text`, centered directly under the headline at y≈150) → content in title / body / caption.
- **Display** only on cover / closing; the **section-opener** heavy uppercase English only on chapter slides.
- **Headline is a full-sentence claim** ("고객의 니즈를 Business Impact로 전환합니다"), not a topic label. Keep to one line (≤ 30 Korean chars).
- **Numbers carry weight:** key figures in display-sm 41 / 800 (`--text` or navy); years in timeline headers at 25 / 600 in navy.
- **English card titles** (Enterprise Experience, Performance Management) in title-tier 600–700, navy. Korean card titles 17 / 700 `--text`.
- **Label** (uppercase, tracked) is reserved for category markers: OUTPUT, PARTNERS, TECH / MANUFACTURING.
- Body baseline 15.2; drop to caption 12.8 only for tags, table cells and chart labels.

---

## 4. Spacing & Density

### 4.1 8px grid

`--space-1` 4 / `--space-2` 8 / `--space-3` 12 / `--space-4` 16 / `--space-5` 20 / `--space-6` 24 / `--space-8` 32 / `--space-10` 40 / `--space-12` 48 / `--space-14` 56 / `--space-16` 64.

### 4.2 Slide-level

- Outer side margin: 56px (content area x=56–1224). Narrative shells use 72px.
- Card gap: 16px (guide `space-4`). Card padding: 20px (guide `space-5`).
- Navy panel padding: 32px (guide `space-6` scaled).
- Title-to-subtitle inside a card: 8px; between bullets: 8px; between tags: 12px.
- Headline block to content: content starts at y=160 (≥ 32px below the headline baseline).

### 4.3 Density floors

- Every card has ≥ 3 layers (e.g., icon or label + title + body, or stat + label + context).
- No text-only body slide: each body slide carries at least one structural visual (navy panel, card grid, table, chevron row, chart, timeline).
- Stat cards always carry context (unit + period or comparator: "665개 프로그램 · 2014–2026").
- Chart containers ≥ 560×300px.

### 4.4 Density vs sparsity

Medium-dense, company-profile density: a typical body slide is a 2–4 column grid filling the full content area (x=56–1224, y=160–640). Generous white comes from the 16px gaps and the white page around filled cards — not from leaving half the slide empty. If content is thin, enlarge the navy panel or the stat, never shrink the grid into the middle.

---

## 5. Layout Grammar (= `recommended_layout_family` vocabulary)

This is the canonical vocabulary `slide-plan` writes into `recommended_layout_family`. Each family bundles 2–8 patterns from `references/patterns.md` that share an information shape.

> **Why family-level, not pattern-level?** `slide-plan` decides the *shape* of information; `/slide` Executor picks the specific pattern based on item count, evidence type, and visual rhythm.

| Family | Patterns (from patterns.md) | Use when | Item-count guide |
|---|---|---|---|
| **structure** | `title`, `section`, `closing`, `agenda` | Deck scaffolding — cover / ABOUT-style section opener / table of contents / closing | 1 hero element |
| **insight** | `hero-statement`, `quote`, `before-after` | One contrast-framed claim ("A보다 B") that needs room | 1 statement + 1 evidence block |
| **breakdown** | `icon-explainer`, `content-cards`, `concept-cards`, `numbered-grid`, `numbered-row`, `two-column`, `checklist`, `bento-grid`, `goal-breakdown`, `kpi-row` | Parallel services, strengths, programmes, competencies | 2×3 grid (signature), 1×3, 1×4 |
| **compare** | `comparison-table`, `comparison`, `two-column` (contrastive) | Level tables (임원 / 부장 / 팀장), as-is vs to-be, option matrices | 2–4 columns |
| **data** | `stats-dashboard`, `chart-bar`, `chart-line`, `chart-pie`, `data-table`, `kpi-row` | 실적 / 비중 / 추이 — the evidence is numeric | 1 chart + takeaway, or 3–4 stat cards |
| **process** | `process-flow`, `numbered-row` (ordered), `agenda` (sequential) | 니즈 진단 → 설계 → 운영 → 성과 평가, timelines, roadmaps | 3–6 chevrons / 3–5 years |
| **visual** | `image-text`, `image-annotated`, `diagram` | Grayscale photo + claim, framework diagram, org / ecosystem map | 1 visual + annotation |

**Layout selection heuristics:**
- 6 parallel services / strengths → `breakdown` (★ `navy-panel-with-card-grid`, 2×3)
- 3–4 parallel items → `breakdown` (`columns-with-vertical-rules` or 1×N filled cards)
- level × competency matrix → `compare` (★ `navy-header-table`)
- methodology stages → `process` (★ `chevron-process-with-output-row`)
- years / history → `process` (`timeline-tiles`)
- 실적 / 비중 → `data` (`chart-led-with-takeaway-stack`)
- single contrast claim → `insight` (`definition-with-side-data`)

**Diversity rules** (enforced in `/slide` Executor):
- No consecutive identical patterns (except `section`)
- Min 3 layout families per deck
- Min 40% pattern differentiation
- Same family ≥ 3 consecutive slides → require justification in `slide_plan.json` (`why_here`)

### 5.1 Hybrid Pattern Catalog — body slide default vocabulary

| Hybrid pattern | Composition | Best-fit roles | Notes |
|---|---|---|---|
| **navy-panel-with-card-grid** ★ | square navy panel in the left third (x=56, w≈360, full content height, `fill=#012281`, `rx=0`) holding a label (accent-soft, label tier), a 2-line claim (white, title/headline tier) and one big figure (white, display-sm); right two-thirds a 2×3 grid of `--surface` filled cards (`rx=12`, no border), each icon 24px + Korean title + 1–2 line body | `concept`, `solution`, `executive_summary`, `evidence` | **Insightlearning signature.** The panel is the slide's one accent event; cards stay monochrome. |
| **navy-header-table** ★ | table with a navy header row (white label text), first column row headers in navy at `fill-opacity=0.7` with white text, body cells `--bg` with `--border` hairlines, square corners | `comparison`, `concept`, `findings` | Use for level tables (임원 / 부장 / 팀장 / 신임) and service × deliverable matrices. Optional: one row lifted to `--accent-soft`. |
| **chevron-process-with-output-row** ★ | row of 4–6 square navy chevrons (white step titles, the first 1–2 "diagnostic" chevrons at `fill-opacity=0.45` with `--text`), under each chevron a `--surface-alt` tile listing activities as `·`-joined noun phrases, and a bottom OUTPUT row (label + deliverables) | `process`, `solution`, `methodology` | The guide's 니즈 진단 → 설계 → 운영 → 평가 page. Chevrons overlap by 12px. |
| **ruled-list-with-eyebrow** ★ | uppercase eyebrow + `--border` hairline + `label : body` rows separated by hairlines, no card boxes | `concept`, `recap`, `solution` | first choice for name + description lists (≥ 4 items) when a card grid would feel heavy |
| **columns-with-vertical-rules** ★ | eyebrow + hairline + 3–4 columns split by vertical hairlines; each column a navy 5px top bar (133px or full column width) + title + body | `concept`, `breakdown`, `executive_summary` | guide's job-competency columns ("bar atop job-competency columns") |
| **chart-led-with-takeaway-stack** | left chart ≈60% (navy opacity ladder) + right 2–3 stacked `--surface` cards (figure / trend / context) | `evidence`, `findings` | data family default |
| **table-with-adjacent-cards** | navy-header table ≈60% + right column of stat cards | `comparison`, `evidence` | |
| **definition-with-side-data** | left claim block (headline-tier navy sentence + body) ≈50% + right stat cards or mini chart | `insight`, `concept` | carries the contrast rhetoric ("A보다 B") |
| **breakdown-with-anchor-stat** | top row of 3–4 stat cards (display-sm figures: 2014 / 665 / 648 / 19,614) + bottom 1×3 explanation cards | `evidence`, `executive_summary` | company-profile "숫자로 보는" page |
| **timeline-tiles** | horizontal navy hairline axis with 4–6 year markers (year 25/600 navy) above `--surface-alt` tiles (`rx=12`); the current / next period tile in `--accent-soft` | `history`, `roadmap`, `process` | "2014 설립 → 2026~ 프로젝트 확대" |
| **photo-with-claim** | grayscale photo at left half (square crop, no rounding) + right claim + 3 `·`-joined key points | `visual`, `insight` | photos stay grayscale; no colour photos on content slides |

**Content shape → first-choice primitive:**

| Content shape | First-choice primitive | Why |
|---|---|---|
| 6 parallel services / strengths / reasons | ★ `navy-panel-with-card-grid` | brand signature; the panel states the claim, cards prove it |
| level × item matrix / service catalogue | ★ `navy-header-table` | the guide's table grammar |
| methodology / project stages | ★ `chevron-process-with-output-row` | process is the message |
| name + description list (4–6) | ★ `ruled-list-with-eyebrow` | lighter than a grid |
| 3–4 parallel pillars | ★ `columns-with-vertical-rules` | navy top bars echo the title rule |
| numeric evidence / share / trend | `chart-led-with-takeaway-stack` | chart drives, cards interpret |
| key company figures | `breakdown-with-anchor-stat` | real figures carry the claim |
| history / roadmap | `timeline-tiles` | years are the axis |
| single contrast claim | `definition-with-side-data` | claim + evidence side by side |

The ★ patterns are first choice **only for their content shape**. The Dominant Primitive Cap (executor.md §0.1 #4) still forbids 3+ consecutive slides on the same primitive.

**Implementation discipline:**
- Navy fields are square (`rx=0`). Rounding only on light cards (`rx=12`), tags (`rx=5`) and the two summary panels (`rx=25`). Icon discs are full circles.
- Cards are filled `--surface`, no border, no shadow.
- Hairlines are `<line stroke="#DFDFDF" stroke-width="1"/>`.
- Lists inside cards are `·`-joined noun phrases, not sentence bullets.

### 5.2 Variation Inspirations (per hybrid pattern)

> Pick ONE variation per body slide (or `표준`); target ≥ 70% non-`표준` across the deck; no variation 3+ times per deck. Accent budget (≤ 2) still applies.

#### `navy-panel-with-card-grid` ★
- **Panel right** — panel moves to the right third, grid on the left.
- **Highlight card** — one grid card lifted to `--accent-soft` with navy title (uses the second accent event).
- **2×2 grid** — four larger cards with 3-line bodies instead of 2×3.
- **Stat panel** — panel holds two stacked figures (display-sm) instead of a claim.
- **Tag footer cards** — each card ends with a row of `--surface-alt` tags (`rx=5`, caption tier).
- **Icon-disc cards** — card icons sit in 40px navy discs (white icon).

#### `navy-header-table` ★
- **Highlight row** — one row in `--accent-soft`.
- **Check-mark matrix** — cells hold navy `tabler-filled/circle-check` icons instead of text.
- **Grouped header** — two header tiers (category / sub-item).
- **Side stat card** — narrow `--surface` stat card to the right of the table.
- **Footer verdict row** — final full-span row with one sentence, `--surface-alt`.
- **No row headers** — plain navy header + body rows (for short lists).

#### `chevron-process-with-output-row` ★
- **Diagnostic lead** — first two chevrons light (navy 0.45), the rest full navy.
- **Icon chevrons** — 24px white icons above step titles.
- **Hero step** — one step's tile 1.5× taller with extra detail.
- **Output cards** — OUTPUT row becomes cards instead of a single line.
- **Vertical** — chevrons stacked vertically on the left, activities to the right.
- **Cycle note** — a bottom `--accent-soft` band stating the feedback loop ("성과 평가 → 다음 과정 설계").

#### `ruled-list-with-eyebrow` ★
- **Hero first row** — first row title-tier with 2-line body.
- **Accent-soft row** — one row on `--accent-soft`.
- **Number column** — right column of figures (navy for the focal one).
- **Two sections** — two eyebrows, `3 + 3` rows.
- **Icon column** — 20px icon column at the left.
- **Verdict band** — last row replaced by an `--accent-soft` band.

#### `columns-with-vertical-rules` ★
- **Full-width top bars** — navy bar spans each column's full width.
- **Numbered eyebrows** — `01 / 02 / 03` prefixes in navy.
- **Bottom KPI row** — one figure per column under a closing hairline.
- **Hero column** — one column 1.6× wider.
- **Accent-soft column** — one column tinted.
- **Tag rows** — each column ends with competency tags.

#### `chart-led-with-takeaway-stack`
- **Mega-number lead** — top takeaway card is a display-sm figure.
- **Two series** — navy 1.0 vs navy 0.45 (분야별 비중 style).
- **Horizontal bars** — ranked categories horizontally.
- **Annotation callout** — one inline callout on the chart.
- **Verdict band** — `--accent-soft` band below the chart.
- **65/35 split** — chart dominant, single takeaway card.

#### `table-with-adjacent-cards`
- **Single tall verdict card** — one tall card replaces stacked cards.
- **Mini-bar column** — inline navy mini-bars in one column.
- **Highlight row** — one row `--accent-soft`.
- **Stat cards row below** — cards move under the table.

#### `definition-with-side-data`
- **Inverted** — data left, claim right.
- **Contrast pair** — claim written as "A보다 B" with A struck in `--text-tertiary` and B in navy.
- **Stacked side data** — mini chart + stat card.
- **Numbered principle** — `01 / 02` eyebrow when part of a series.

#### `breakdown-with-anchor-stat`
- **Navy stat strip** — the stat row sits in a full-width navy band (white figures) — one accent event.
- **Stat with comparator** — "2023 → 2026" pair with arrow.
- **Asymmetric cards** — `2fr : 1fr : 1fr`.
- **Trend annotation** — `↑` in `--positive` on one stat (data only).

#### `timeline-tiles`
- **Current-period highlight** — latest tile `--accent-soft`.
- **Milestone figures** — each tile carries one figure.
- **Two-row timeline** — events above and below the axis.
- **Future dashed** — future years with a dashed-free lighter tile (`--surface-alt`), never dashed strokes.

#### `photo-with-claim`
- **Photo right** — mirror layout.
- **Navy wash caption** — a navy caption block overlapping the photo's bottom edge (square).
- **Three key-point cards** — points become three small cards.
- **Full-width photo strip** — photo becomes a top strip (h≈200) with the claim below.

---

## 6. Header / Body / Footer Structure

### 6.0 Shell composition (narrative band vs content light)

| Shell | Band? | Fill | Signature elements | Text color |
|---|---|---|---|---|
| `01_cover` | yes | `#012281` field cut by a diagonal edge (820→660), `#01185A` right panel | thin sky stripe along the diagonal; eyebrow uppercase sky, tracking 7; title display white; second line sky; right panel is the photo slot (grayscale photo + navy wash when available); logo top-left when supplied | white / sky / `#B3BDD9` |
| `02_chapter` | partial | white page + square navy block x=0–440 full height | sky number square (128px) with white light number; English uppercase section title 56/900 black (`{{CHAPTER_LABEL}}`, e.g. "ABOUT COMPANY"); Korean title in navy beneath (`{{CHAPTER_TITLE}}`); short 5px navy rule; summary in body | black / navy / `#595959` |
| `03_content` | no (light) | `#FFFFFF` | slide label 22/300 top-left at y=60 (`{{PAGE_EYEBROW}}`, e.g. "회사 소개"); title rule = 133×5 navy segment + 2px navy line to x=1224 at y≈72–77; headline 30/800 centered at y=130; free content region x=56 y=160 w=1168 h=480; GM line centered y=680; page number bottom-right | black / `#595959` / `#666666` |
| `04_ending` | yes | full `#012281` | everything centered; sky tracked eyebrow + 80px sky rule; display headline white; sky highlight line; contact line; logo centered above the eyebrow when supplied | white / sky / `#B3BDD9` |

### 6.1 Page anatomy (1280×720)

```
Content slide (03_content)
┌──────────────────────────────────────────────────────────┐
│ 회사 소개                         ← slide label (y≈60)    │
│ ▬▬▬▬━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ← navy rule (y 72–77)  │
│        고객의 니즈를 Business Impact로 전환합니다          │ ← headline centered (baseline 130)
│                                                          │
│  Body / content area  (x 56–1224, y 160–640, h 480)      │
│                                                          │
│            GM line (centered, baseline 680)        03/12 │
└──────────────────────────────────────────────────────────┘
```

Narrative shells (cover / chapter / closing) have no label, rule, GM or body zone — see §6.0.

### 6.2 Header zone

- **Always present on content slides** (it is the shell): slide label + navy title rule.
- `{{PAGE_EYEBROW}}` carries the Korean section name ("회사 소개", "서비스", "실적"), not an uppercase taxonomy tag. Same label for every slide in a section.

### 6.3 Title zone

- **Content:** headline is one centered sentence-claim, ≤ 30 Korean chars, one line, no `<br>`.
- Optional **lead** sentence (body 15.2 `--text`, centered, y≈150) explaining *how*; when used, start the body at y=176.
- **Cover / closing:** display 52/700 white, left-aligned on the cover, centered on the closing.
- **Chapter:** English uppercase title + Korean title beneath (see §6.0).

### 6.4 Body zone

- Body fills the content area x=56–1224, y=160–640 top-down; grids stretch to the full width.
- Columns align to the 1168px width with 16px gaps (2 cols: 576; 3 cols: 378.7; 4 cols: 280).
- Navy panel width for the signature layout: 360px.

### 6.5 GM (governing message) line

- **Voice:** consultative, confident, polite declarative (~합니다 / ~하겠습니다), contrast-framed, first-person corporate — the company speaks as 인싸이트러닝 and calls the client 고객사, Korean HRD consulting proposal / company profile, English for programme names, frameworks and section titles
- **Composition hint:** One polite declarative sentence (~합니다) stating the business impact for 고객사; contrast framing ('A보다 B') welcome; real figures only; never a restatement of the headline.
- **Forbidden phrases:** "여러분", "당신"

- **Position:** centered at x=640, baseline y=680 (shell).
- **Typography:** body 15.2 / 700 / `--text-secondary`.
- **Length:** ≤ 40 Korean chars, one line.
- **Cardinal rule:** never restate the headline — the headline is the claim, the GM is the business so-what for 고객사.

### 6.6 Footer / page number

- Page number bottom-right, caption 12.8 `--text-tertiary`, format `03 / 12`.
- Logo (`insightlearning-logo-color.png` on light, `-white.png` on navy) only on cover (top-left) and closing (centered); never on content slides. Never recolour or redraw the swoosh. (Logo files are not in the repo yet — omit the logo until they are supplied.)

---

## 7. Page Flow (Title → Body → End)

| `page_family` | Layout templates | Typical position | Required fields |
|---|---|---|---|
| `title` | `01_cover.svg` | slide 1 | eyebrow + title (+ sky second line) + subtitle + presenter/date; no GM |
| `body` | `03_content.svg` + family templates | slides 2 to N-1 | slide label + headline claim + body + GM |
| `chapter` | `02_chapter.svg` | between major divisions | number + English uppercase title + Korean title (+ summary); no GM |
| `end` | `04_ending.svg` | slide N | closing headline + sky line + contact; no GM |

**Flow conventions:**
- Cover → optional agenda (body, `agenda` pattern, English section names with Korean captions) → sections opened by chapter slides → closing.
- Chapter slides at every major section for decks ≥ 10 slides (company-profile rhythm: ABOUT COMPANY / OUR SERVICE / OUR EXPERIENCE). Optional below 8 slides.
- Closing slide: thank-you / contact; the navy closing may carry a blue-tinted grayscale photo when available.

---

## 8. Chart & Table Treatment (Rhetorical Roles → Visual Implementation)

This preset honors the 9 rhetorical roles defined in `references/chart-rhetorical-roles.md`. Below is the preset-specific implementation layer.

### 8.1 Role → primary chart template

| `chart_strategy` | Primary | Alt |
|---|---|---|
| `growth-trend` | `chart-bar` (yearly navy bars — the profile's 실적 pages) | `chart-line` |
| `forecast` | `chart-bar` with future bars at navy 0.25 | `timeline-tiles` |
| `structural-break` | `chart-line` with a vertical break line + annotation | `data-table` before/after |
| `focus-comparison` | `chart-bar` with the focus bar navy, others navy 0.25 | `navy-header-table` with highlight row |
| `distribution` | horizontal `chart-bar` | `data-table` |
| `quadrant` | `diagram` (matrix_2x2) | `navy-header-table` 2×2 |
| `priority-matrix` | `navy-header-table` with check icons | `diagram` |
| `split-segment` | `chart-pie` / donut (≤ 5 segments, navy opacity ladder) — 분야별 비중 | stacked `chart-bar` |
| `funnel` | `diagram` (funnel) | `chevron-process-with-output-row` |
| `custom` | closest pattern; document in `chart_takeaway` | — |

### 8.2 Chart styling rules

- **Palette:** single-accent opacity ladder using `#012281`
- **Semantic exception:** `#059669` / `#E11D48` / `#D97706` only when color encodes data meaning

- Inline data labels (caption 12.8, `--text`; focus value navy bold) — no side legend unless 2 series, then a single inline legend row.
- Axis ticks / labels `--text-tertiary` caption; gridlines `--border` 1px; no axis box.
- Square bars (`rx=0`). No drop shadows, 3D, gradients or glow.

### 8.3 Table styling rules

- **Header row:** navy fill, white label text (title-tier 600), square corners.
- **Row headers:** first column navy at `fill-opacity=0.7` (stand-in for the guide's steel) with white text.
- **Cells:** `--bg`, `--border` 1px hairlines, caption–body tier; numerics right-aligned.
- **Recommended row/column:** `--accent-soft` fill (one only).
- **Verdict row:** optional final row on `--surface-alt` with one sentence.

### 8.4 Required adjacency: chart + takeaway

Every `data` family slide pairs its chart with a takeaway: right column stack (`--surface` cards: display-sm figure + label + context line) or an `--accent-soft` verdict band directly below the chart. A chart without a takeaway fails Layer 1 R2 at plan time.

---

## 9. Icon System

### 9.1 Library lock

- **Default:** tabler-outline
- **Fallback:** tabler-filled
- **Forbidden:** other packs, emoji, unicode glyph icons, mixed packs.

### 9.2 Usage

```xml
<use data-icon="tabler-outline/<name>"
     x="..." y="..." width="24" height="24"
     stroke="currentColor" stroke-width="2" color="#000000"/>
```

`finalize_svg.py` resolves the placeholder at post-processing. Use `tabler-filled/<name>` (navy) only for solid process-column icons and check marks. Brand pictograms: globe `world`, chip `cpu`, rising chart `chart-arrows-vertical`, person `user`, handshake `heart-handshake`, magnifier `search`, target `target`, bulb `bulb`.

### 9.3 Search before use

```bash
ls assets/icons/tabler-outline/ | grep <keyword>
```

### 9.4 Sizing

- Card icon: 24px, stroke 2, `--text`.
- Icon disc: 40–56px navy circle with a white 24–28px icon (optional `--border` 2px ring).
- Process-column solid icon: 28px navy (`tabler-filled`).
- Inline icon: 16px.

### 9.5 Icon vs number badges

- Icons for service / strength / competency cards.
- Number badges (`01`–`06`, light weight, navy) when order matters: reasons ("5가지 이유"), process steps, section numbers.
- Mixing is fine across slides; within one grid use one kind.

### 9.6 Icon wrappers / decorations

Allowed: bare line icons on cards, or white icons in **navy discs** (the brand's only wrapper). Forbidden: coloured or semantic-soft badges, rounded-square icon tiles, sky-coloured icons on content slides.

---

## 10. Anti-Patterns (Reject at Plan Time)

| # | Anti-pattern | Detect via | Fix |
|---|---|---|---|
| A1 | Same family 3+ consecutive slides | `recommended_layout_family` streak | vary family or justify in `why_here` |
| A2 | Dominant primitive 3+ consecutive (navy-panel / card-grid / table / chevron / chart) | executor.md §0.1 #4 | rotate primitive |
| A3 | Same §5.2 variation 3+ times | per-slide variation audit | pick another variation |
| A4 | Chart without takeaway | `chart_strategy` set, `chart_takeaway` empty | add takeaway card or verdict band |
| A5 | Empty `evidence_sources` / invented figures | array empty or figure not in source | cite source or mark `inference`; never invent numbers |
| A6 | Multi-hue chart palette (sky / chart-blue / steel / rainbow on content) | non-token hex in chart | navy opacity ladder |
| A7 | Sky (`#58CCFF`) on a content slide or on white | hex scan of body slides | sky lives on narrative navy shells only |
| A8 | Multi-icon-pack mixing / emoji | icon prefixes, emoji codepoints | tabler-outline (+ filled for solid) only |
| A9 | Headline is a topic label, not a claim | headline lacks a predicate (~합니다) | rewrite as one sentence-claim |
| A10 | GM restating the headline | > 60% token overlap | rewrite as business so-what |
| A11 | Forbidden voice | "여러분", "당신", casual endings (~해요, ~하자) | polite declarative, "고객사" |
| A12 | Sentence bullets in cards | list items with periods / full sentences | `·`-joined noun phrases |
| A13 | Rounded navy fields | navy rect with `rx>0` (except the two summary panels rx=25) | square navy |
| A14 | Shadows / gradients / glow | `filter`, `linearGradient`, `radialGradient` | flat colour fields + hairlines |
| A15 | 3+ accent events on one slide | navy fields + accent-soft + navy text > 2 | cut to ≤ 2 |
| A16 | Text-only body slide | no panel / card / table / chart / chevron / timeline | add a structural visual |
| A17 | Colour photography on content slides | image block not grayscale | grayscale photo |
| A18 | Off-palette hex | hex outside §2.1 | map to nearest token |

---

## Appendix — `slide-plan` quick reference

**Family vocabulary** (use one per slide): `structure` / `insight` / `breakdown` / `compare` / `data` / `process` / `visual`.

**Chart strategy vocabulary**: see `references/chart-rhetorical-roles.md`.

**Page family** (use one per slide): `title` / `chapter` / `body` / `end`.

**Slide role enum**: see `references/slide-role-enum.md`.

---

<!-- Authored by /theme-init (Step 4 + 5d) from the Insightlearning design guide (README.md + tokens.json, 2026 company profile). -->
