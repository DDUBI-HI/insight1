# DESIGN.md — Insightlearning

> Preset-level design vocabulary for `slide-plan` consumption.
> Pairs with `theme-active.json` (token SSOT) and `references/patterns.md` (HTML pattern catalog).
>
> **Purpose:** Give `slide-plan` the structured vocabulary it needs to produce `slide_plan.json` entries (`recommended_layout_family`, `chart_strategy`) that `/slide` Executor can consume without re-deciding visual style.
>
> **Scope:** Insightlearning only. Other presets supply their own `DESIGN.md` via `/theme-init`.
>
> **Source:** `Insightlearning-design-system` (tokens.json v1 + 10 component specs + logos, derived from the 2026 company profile, 1440×810). Values are scaled ×0.889 to the locked 1280×720 canvas. Page references (`p.N`) point at the company-profile PDF; component names (`SlideTitle`, `NavyPanel`, …) point at the design-system package — see §11.

---

## 1. Visual Theme & Atmosphere

- **Tone:** confident, consultative, performance-oriented. Korean B2B HRD proposal register.
- **Reference moodboard:** Korean corporate company profile / HRD consulting proposal — deep navy brand blocks, white pages, centered declarative headlines, structured tables and step chevrons (p.8, p.10, p.14).
- **Atmosphere:** orderly, trustworthy, "we have done this 665 times." Every page reads as an answer to a client's question — what it is, how it works, what it produced. White space is generous but every body page carries a structured block (table, step band, stat panel, card stack).
- **Anti-mood:** startup pitch-deck flash, playful illustration, rainbow infographics, dark-mode tech decks, editorial magazine minimalism with no structure.
- **One-line litmus:** If a slide could be inserted into the 2026 Insightlearning company profile without the client noticing a different author, it passes.

**Voice anchors (from theme-active.json):**
- **Tone:** confident, consultative, performance-oriented
- **Point of view:** first-person corporate (company as subject)
- **Register:** Korean B2B HRD proposal / company profile, formal 합니다체

---

## 2. Palette & Contrast Behavior

### 2.1 Allowed colors (literal, locked)

This preset is monochrome + single accent. The ONLY hex values that may appear in any generated SVG / CSS / Chart.js palette are:

| Token | Hex | Role |
|---|---|---|
| `--bg` | `#FFFFFF` | page background |
| `--surface` | `#FFFFFF` | card / container |
| `--surface-alt` | `#F8F8F8` | grouped row / nested card |
| `--text` | `#1A1A1A` | primary text |
| `--text-secondary` | `#595959` | secondary text |
| `--text-tertiary` | `#666666` | captions, page numbers |
| `--border` | `#DFDFDF` | default divider |
| `--border-strong` | `#C2C2C2` | emphasis divider |
| `--accent` | `#012281` | sole brand pointer |
| `--accent-soft` | `#E0EDF3` | accent-tinted highlight bg |
| `--accent-ink` | `#1F375D` | accent pressed / dark |
| `--positive` | `#059669` | data context only |
| `--negative` | `#E11D48` | data context only |
| `--warning` | `#D97706` | data context only |

Narrative shells only (cover / chapter / ending — Rule T9): `shell-bg #012281`, `shell-text #FFFFFF`, `shell-text-secondary #D2D6E3`, `shell-accent #58CCFF`. Sky `#58CCFF` never appears on a content slide.

### 2.2 Contrast & accent budget

- **≤ 2 accent events per content slide** (anti-slop-theme Rule T2). Shell chrome — the split navy rule under the section label — is not counted.
- **A navy block counts as ONE event**, including its opacity-ladder siblings. DS `steel #486FB0` (DataTable row-header cells) is rendered as `#012281` at `fill-opacity` 0.72 (visually ≈ #4860A4) and DS `chart-blue #58A6F6` (second chart series) as `#012281` at 0.45 — the single-accent lock forbids those literals on content slides. The whole navy block is one event.
- **Sky `#58CCFF` lives on navy only** (DS rule: never text on white, 1.8:1) — on content slides it may appear only inside a navy block (NavyPanel labels, the short rule under a panel title). DS `ProcessSteps variant="diagnostic"` (sky chevrons on white) is rendered with `accent-soft #E0EDF3` chevrons + `#1A1A1A` text, ending in a navy outcome step.
- **Typical budget split:** one navy structural block (label column, stat panel, chevron row, or focus bar) + one emphasis (accent text on a key number, or one `accent-soft` highlight row/column).
- **White text on navy** is the only text-on-accent combination. Sky text is shell-only.
- **Semantic colors** (`#059669` / `#E11D48` / `#D97706`) only when color encodes data meaning (growth/decline/risk). Never to differentiate cards.
- **Chart palette:** single-accent opacity ladder on `#012281` — 1.0 / 0.70 / 0.45 / 0.25.

### 2.3 Background hierarchy

`bg #FFFFFF` (page) → `surface-alt #F8F8F8` (filled cards, grouped rows) → `accent-soft #E0EDF3` (one highlight row / recommended column) → `accent #012281` (one structural navy block with white text).

- Cards are **filled** (`#F8F8F8`, no border — Card Treatment Lock). Do not draw a 1px border on a filled card.
- Never stack `accent-soft` inside `accent-soft`, and never place a `surface-alt` card on top of a navy block.
- Table cells sit on `#FFFFFF` with `#DFDFDF` hairlines; the label column is navy (p.10).

---

## 3. Typography Hierarchy

### 3.1 Font chain (locked)

```
Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif
```

Every `<text>` element in generated SVG uses this exact chain.

### 3.2 Type scale

| Role | Size (px) | Weight | LH | Tracking | Use |
|---|---|---|---|---|---|
| Display | 56 | 800 | 1.08 | -1.68 | title slide hero |
| Display-sm | 40 | 800 | 1.1 | -0.8 | hero stat / closing accent |
| Headline | 29.6 | 800 | 1.3 | -0.89 | centered SlideHeading (DS `headline` 33px ExtraBold, -0.03em) |
| Title | 17.6 | 700 | 1.4 | 0.0 | Korean card / panel title (DS `card-title`) |
| Body | 15.2 | 400 | 1.65 | -0.3 | card text, bullets (DS `body`, -0.02em) |
| Caption | 12.8 | 400 | 1.6 | 0.0 | tags, table cells, chart labels (DS `small`) |
| Label | 12.8 | 600 | 1.3 | 0.26 | uppercase category labels — OUTPUT, PARTNERS (DS `label`) |

Shell-only literals (DS): cover eyebrow 17.6/400 tracking 7 (0.4em) sky; cover hero 52/700 -1.56; SlideTitle label 24/300 -0.48; chapter display title 52/900 uppercase; chapter Korean subtitle 24/700 navy; section number 40/300.

DS secondary inks not in the token contract: `ink-strong #333333` (stat numbers, Korean card titles) and `ink-navy` = `accent-ink #1F375D` (English card titles). `#333333` may be used as a text literal for numbers / card titles; list it in `.theme-color-allow` if the strict theme check flags it.

### 3.3 Hierarchy rules

- **Display (56)** only on cover / chapter / closing shells. Body slides never use Display.
- **Display-sm (40/800)** for hero numbers inside a navy stat panel (p.20 "665") or a KPI strip (p.3 "2014 / 10+ / 100+"). One hero number per slide.
- **Headline (32/700)** is always the centered page title (shell `{{PAGE_TITLE}}`). One line only — no line breaks (A15).
- **Section label** (24/300 Light — never bold, top-left, `{{PAGE_EYEBROW}}`) names the chapter context in the brochure's form: `SOLUTION 01 | 리더십 & 조직역량`, `회사 소개`, `수행 실적`. Pipe-separated, sentence case.
- **Lead sentence** (15.2/400, `#595959`, centered at y=152) is optional and explains the headline in one line (p.10, p.20). It is not the GM.
- **Block eyebrow** (Label 12.8/600, uppercase, `#012281` or `#595959`) names a block in `ENGLISH | 한국어` form: `LEVEL-BASED ROADMAP | 계층별 리더십` (p.10). Max one accent-colored eyebrow per slide.
- **Body baseline 15.2**; raise to 18.4 only on low-density slides (≤ 3 items).
- English product/program names (`Leadership Café-teria`, `Job Competency Cafe-teria`, `Extended DISC`) stay in English; do not translate.

---

## 4. Spacing & Density

### 4.1 8px grid

`--space-1` 4 / `--space-2` 8 / `--space-3` 12 / `--space-4` 16 / `--space-5` 20 / `--space-6` 24 / `--space-8` 32 / `--space-10` 40 / `--space-12` 48 / `--space-14` 56 / `--space-16` 64.

### 4.2 Slide-level

- Outer margin: 56px left/right (content x=56–1224). Body blocks commonly inset to x=96–1184 (brochure p.10 inset), which reads more centered under the centered headline.
- Content region: y=168–640 (below headline + optional lead, above GM).
- Card padding: 24px; filled-card stack gap: 16px; column gutter: 48–56px between left and right blocks.
- Table row height: 56–60px; label column 160–176px wide.

### 4.3 Density floors

- Every body slide carries ≥ 1 structured block (table / step band / stat panel / chart / diagram / filled-card stack) — no headline + bullets slides.
- Filled cards hold ≥ 2 layers: bold title (15.2–18.4/700) + one gray descriptor line (`#595959`). Title-only cards are rejected.
- Stat panels pair each number with a one-line unit/description (p.20 "6 · 년 연속 수행").
- Charts carry a legend-dot title (`■ 연도별 수행 프로그램 수`) and data labels on bars.

### 4.4 Density vs sparsity

Medium-high density, but organised: a brochure page holds 2 blocks side by side (p.10, p.13, p.20) or 1 wide block + 1 band (p.8, p.14). Empty white is fine around the centered headline; do not fill it with decorative graphics. If a slide has only one thought, use a hero-stat or chapter page instead of padding a body slide.

---

## 5. Layout Grammar (= `recommended_layout_family` vocabulary)

This is the canonical vocabulary `slide-plan` writes into `recommended_layout_family`. Each family bundles patterns from `references/patterns.md` that share an information shape.

> **Why family-level, not pattern-level?** `slide-plan` decides the *shape* of information; `/slide` Executor picks the specific pattern based on item count, evidence type, and visual rhythm.

| Family | Patterns | Use when | Item-count guide |
|---|---|---|---|
| **structure** | `title`, `section`, `closing`, `agenda` (photo-card row, p.2) | Cover / chapter / closing / table of contents | 1 hero element; agenda 3–5 cards |
| **insight** | `hero-statement`, `before-after`, `definition-with-side-data` | One message that must land (mission, positioning, "why us" thesis) | 1 statement + 1 evidence block |
| **breakdown** | `filled-card-stack`, `icon-grid-with-navy-intro`, `kpi-strip`, `columns-with-vertical-rules`, `ruled-list-with-eyebrow` | N parallel services, themes, strengths, clients | 3–6 items |
| **compare** | `navy-label-table`, `comparison-table`, `two-column` | A vs B, level × content matrix, options | 2–4 columns or 4–7 rows |
| **data** | `navy-stat-panel-with-charts`, `chart-bar`, `chart-line`, `chart-pie`, `data-table` | Track record, counts, shares, trends | 1 stat panel + 1–2 charts |
| **process** | `chevron-step-band`, `year-timeline-columns`, `process-flow` | Methodology steps (1–4 STEP), company history, program schedule | 3–5 steps / 3–5 eras |
| **visual** | `hub-and-satellite`, `diagram`, `image-text` | Strength wheel, system / relationship diagram, photo-led page | 1 primary visual + 2–4 annotations |

**Layout selection heuristics:**
- methodology / 진단→설계→실행→평가 → `process` (`chevron-step-band`)
- history by year → `process` (`year-timeline-columns`)
- level/role × content → `compare` (`navy-label-table`)
- 3–6 parallel themes with a short descriptor each → `breakdown` (`filled-card-stack`)
- 4 service areas with icons → `breakdown` (`icon-grid-with-navy-intro`)
- 3–4 headline numbers → `breakdown` (`kpi-strip`) or `data` (`navy-stat-panel-with-charts` when charts exist)
- "5 reasons / strengths" around one core → `visual` (`hub-and-satellite`)
- single positioning statement → `insight`

**Diversity rules** (enforced in `/slide` Executor):
- No consecutive identical patterns (except `section`)
- Min 3 layout families per deck
- Same family ≥ 3 consecutive slides → require justification in `slide_plan.json` (`why_here`)
- Dominant Primitive Cap: no 3 consecutive body slides with the same dominant primitive

### 5.1 Hybrid Pattern Catalog — body slide default vocabulary

Brochure body pages are almost always **two blocks** (left/right) or **one band + one row** — never a lone card grid. These hybrids are the default starting points.

| Hybrid pattern | Composition | Best-fit roles | Notes |
|---|---|---|---|
| **navy-label-table** ★ | block eyebrow (`ENGLISH \| 한국어`, accent) + table: left label column filled `#012281` (top row 1.0, other rows `fill-opacity` 0.70) with white centered labels, right value cells white with `#DFDFDF` hairlines, centered body text. | `comparison`, `concept`, `solution` (level × content, role × program) | Brochure signature (p.10). The navy column = 1 accent event. Pair with a `filled-card-stack` on the right when there is a second axis (theme vs level). |
| **filled-card-stack** ★ | block eyebrow + vertical stack of 3–5 `#F8F8F8` filled cards (no border, radius 14 — DS `InfoCard`), each = bold title (15.2/700, English OK) + gray descriptor line. | `concept`, `solution`, `summary` | Brochure signature (p.10 right, p.13). First choice for list-of-items with name + description. |
| **chevron-step-band** ★ | row of 4 navy chevron arrows (`STEP 1…4`, white label, opacity ladder 1.0→0.70 optional) + under each arrow a column: line icon (navy) + bold step name + 3–4 dot bullets + hairline + `OUTPUT` label + deliverable line. | `process`, `methodology`, `solution` | Brochure signature (p.8, p.14, p.16). Genuine sequences only (Rule 20). The chevron row = 1 accent event. |
| **navy-stat-panel-with-charts** | left navy panel (square; `radius 28` only for the summary variant — DS `NavyPanel rounded`) with eyebrow (white 0.7), hero number (Display-sm, white), divider, 3 stat rows (number + label); right 1–2 charts (bar = accent ladder) with legend-dot titles. | `evidence`, `findings`, `proof` | p.20, p.21. Panel = event 1, focus bars = event 2. |
| **icon-grid-with-navy-intro** | left navy panel (40%) holding intro line + kicker; right 2×2 grid of icon + bold service name + 2-line gray descriptor (no card boxes). | `solution`, `concept` (service catalog) | p.9, p.11, p.18. Icons navy line-art. |
| **kpi-strip** | 3–4 `#F8F8F8` filled boxes in a row, each = Display-sm number (navy) + small caption (`회사 설립`, `YEARS`, `CLIENTS`), paired with a text block or photo-free statement on the left. | `insight`, `executive_summary`, `about` | p.3. Add a supporting sentence block; never the strip alone (Rule 19). |
| **year-timeline-columns** | horizontal line with year nodes (navy dot + bold year, latest year in accent with "→"), below each node a gray-bordered column of dot bullets. | `roadmap`, `history`, `context` | p.6. Max 5 eras. |
| **hub-and-satellite** | central circle (soft gray ring) titled `우리의 강점` + 4–6 satellite navy-circle icons on an orbit; left/right side blocks with underlined bold titles + 2–3 bullet lines each. | `insight`, `comparison` ("why us") | p.7. Satellites = 1 accent event (same navy). |
| **definition-with-side-data** | left statement block (bold title + 3–4 line paragraph) + right labeled rows (`Vision` / `Mission` / `Core Value` with hairline separators). | `insight`, `context` | p.5 (rendered light — no photo background on content slides). |
| **sector-list-with-partner-card** | left ruled list: navy uppercase sector label + gray client names per row; right `#F8F8F8` card listing partners as label : value rows. | `proof`, `team`, `evidence` | p.19. |
| **ruled-list-with-eyebrow** / **columns-with-vertical-rules** | eyebrow + hairline rows/columns, no boxes | generic list-of-items / parallel components | Inherited editorial fallback when the content does not match a brochure signature. |

**Rule of thumb for picking within a family:**
- `compare` with a level/role axis → **`navy-label-table`** (★)
- `breakdown` list-of-items with name + description → **`filled-card-stack`** (★); service catalog with icons → `icon-grid-with-navy-intro`
- `process` with 3–5 ordered steps → **`chevron-step-band`** (★); years → `year-timeline-columns`
- `data` → `navy-stat-panel-with-charts`
- `insight` → `definition-with-side-data` or `kpi-strip` + statement

| Content shape | First-choice primitive | Pattern |
|---|---|---|
| list-of-items with name + description (3–5) | `boxed-cards` (filled) | `filled-card-stack` |
| level / role × content matrix | `table-led` | `navy-label-table` |
| ordered methodology (3–5 steps) | `process-flow` | `chevron-step-band` |
| numeric track record / counts / shares | `chart-led` | `navy-stat-panel-with-charts` |
| 3–4 headline numbers, no series | `boxed-cards` | `kpi-strip` |
| service catalog (4 areas) | `boxed-cards`-free icon grid | `icon-grid-with-navy-intro` |
| strengths around one core | diagram | `hub-and-satellite` |
| history by year | `process-flow` | `year-timeline-columns` |

The three ★ patterns are the brochure's signature, not a universal default — the Dominant Primitive Cap (executor §0.1 #4) still forces rotation.

### 5.2 Variation Inspirations (per hybrid pattern)

Pick ONE per body slide (or `표준`). Target ≥ 70% non-`표준` across the deck; no variation 3+ times per deck; accent ≤ 2 still holds.

**navy-label-table**
- *paired card stack* — table left (55%) + `filled-card-stack` right (p.10 full form)
- *two-tier label* — label column shows role + small caption (years / headcount)
- *highlight row* — one value row in `accent-soft` for the recommended level (replaces ladder → navy column stays 1.0 only)
- *column headers* — add a header row (`#F8F8F8`, label typography) for 2+ value columns
- *verdict line* — bold one-line conclusion under the table

**filled-card-stack**
- *English title + Korean descriptor* (p.10 `Future Excellence` style)
- *icon-led cards* — 24px navy icon left of title
- *numbered cards* — `01–04` navy number when order matters
- *2×2 card grid* instead of a single column (p.13 left)
- *accent-soft lead card* — first card `accent-soft` as the recommended item

**chevron-step-band**
- *OUTPUT row* — deliverable per step under a hairline (p.8)
- *two-line chevron* — `STEP n` + step name inside the arrow (p.14)
- *diagnostic side panel* — chevrons + bottom-right navy panel listing tools (p.14 `DIAGNOSTIC TOOLS`)
- *icon row* — navy line icons between chevron and step name
- *ladder fill* — chevrons 0.45 → 1.0 left to right to show progression

**navy-stat-panel-with-charts**
- *panel + bar + horizontal bar* (p.20 full form)
- *panel + single chart + legend-dot title*
- *panel + ranked horizontal bars* with focus bar
- *compact panel* — hero number only + chart takes 70%
- *stat panel + certification band* (p.21 bottom band)

**icon-grid-with-navy-intro**
- *navy panel left* (p.9) / *navy panel top-left inset* (p.11)
- *2×3 grid* for 6 areas (p.18)
- *bullet-dense cells* — 3 descriptor lines per cell
- *caption tags* under each cell

**kpi-strip / year-timeline-columns / hub-and-satellite / definition-with-side-data / sector-list**
- kpi-strip: *with statement block left* · *with English caption* · *4-up* · *accent number on one box only*
- year-timeline: *latest era in accent with arrow* · *bordered columns* · *era subtitle under year* · *3 eras only*
- hub-and-satellite: *side blocks with underline titles* · *4 satellites* · *6 satellites* · *center caption 'Strength'*
- definition-with-side-data: *Vision/Mission/Core Value rows* · *two-paragraph statement* · *quote line under title*
- sector-list: *4 sectors* · *partner card with 'PARTNERS' eyebrow* · *count tag per sector*

---

## 6. Header / Body / Footer Structure

### 6.0 Shell composition (narrative band vs content light)

Composed in Step 5 — source at `templates/layouts/insightlearning/_shell_src/*.tpl.svg`.

| Shell | Band? | Fill | Signature elements | Text color |
|---|---|---|---|---|
| `01_cover` | Yes, full-bleed | `shell-bg #012281` + right wedge `accent-ink #1F375D` + thin diagonal sky stripe `#58CCFF` (12px, x 824→1060) | White logo top-left; eyebrow 17.6/400 tracking 7 sky (y=232); two-line white hero 52/700 (y=316 / 380); white lead (y=440); presenter · date (y=656). Wedge stands in for the grayscale photo (p.1). | white / `#D2D6E3` / sky eyebrow |
| `02_chapter` | Half band (DS `SectionOpener`, tone sky) | left 560px `#012281` (navy-washed photo stand-in), right `#FFFFFF` | Square sky number block 128×128 straddling the edge at (496,272), numeral 40/300 white (decoration); uppercase English display title 52/900 `#1A1A1A` at x=672, y=348; Korean subtitle 24/700 navy (y=392); summary body gray (y=440). (p.3, p.9) | `#1A1A1A` + navy on light; white on sky block |
| `03_content` | **No** (light) | `#FFFFFF` | SlideTitle label top-left (24/300, y=62) → double navy rule (136×6 bar + 2px line to x=1224, y=72–78) → centered SlideHeading 29.6/800 (y=128) → optional centered lead (y=158) → free content x=56, y=168, w=1168, h=472 → GM centered y=680 (`#595959`, 700) → page number y=696 right. (p.10, p.20) | `#1A1A1A` / `#595959` / accent |
| `04_ending` | Yes, full-bleed | `#012281` | Centered sky frame (800×512, 8px stroke); sky tracked label, white Display headline, sky Display-sm accent, light contact line, presenter · date at y=672. (p.26) | white / sky / `#D2D6E3` |

### 6.1 Page anatomy (1280×720)

```
y=0    ┌─────────────────────────────────────────────────────────┐
y=62   │ SECTION LABEL (24/300 Light)                            │  header
y=72–78│ ████████────────────────────────────────────────────── │  split navy rule
y=128  │              CENTERED HEADLINE (29.6/800)               │  title
y=158  │              centered lead sentence (15.2, gray)        │  optional
y=168  │                                                         │
       │   BODY: 1–2 structured blocks (x=56..1224)              │  body
y=640  │                                                         │
y=680  │              GM line (15.2/700, #595959, centered)      │
y=696  │                                                  NN     │  page no.
y=720  └─────────────────────────────────────────────────────────┘
```

Narrative shells drop the header/rule/GM and use the band compositions in §6.0.

### 6.2 Header zone

Always present on content slides: section label (`{{PAGE_EYEBROW}}`) + split navy rule from the shell. The label is the chapter/section context in the brochure form `SOLUTION 02 | AI /AX`, not an uppercase eyebrow. Never leave it empty.

### 6.3 Title zone

- Content: one centered Headline line (≤ ~34 Korean chars at 32px). No line breaks; shorten instead.
- Optional lead sentence at y=152 — explains or names the program (`Leadership Café-teria — …`).
- Cover / chapter / closing titles use Display on the band, left-aligned (cover, chapter) or centered (closing).

### 6.4 Body zone

- Region x=56..1224, y=168..640. Prefer the brochure's two-block composition (left 55% / right 40% with 48–56px gutter) or one full-width block + one band.
- Blocks are vertically top-aligned at y≈200 (eyebrow at y≈188). Do not vertically center thin content in the middle of the page; leave whitespace below.

### 6.5 GM (governing message) line

- **Voice:** confident, consultative, performance-oriented, first-person corporate (company as subject), Korean B2B HRD proposal / company profile, formal 합니다체
- **Composition hint:** One declarative sentence naming the business impact or so-what, formal Korean (…합니다 / …입니다 or noun ending). Never a restatement of the page title. ≤35 chars ideal.
- **Forbidden phrases:** _(none)_

Position: x=640, y=680, `text-anchor="middle"`, 15.2/700, `#595959`. One line, ≤ 35 chars ideal (≤ 45 max). It states the client-facing impact (`리더십 교육을 조직의 실제 성과 행동으로 연결합니다`), never the page title.

### 6.6 Footer / page number

Page number: caption 12.8/500, `#666666`, x=1224, y=696, right-aligned, two digits. No brand logo on content slides (the brochure places the logo only on cover / closing / long tables). No footer rule.

---

## 7. Page Flow (Title → Body → End)

| `page_family` | Layout templates | Typical position | Required fields |
|---|---|---|---|
| `title` | `01_cover.svg` | slide 1 | eyebrow (English, tracked), title (1–2 lines), subtitle, presenter · date; no GM |
| `body` | `03_content.svg` + family templates | slides 2 to N-1 | section label, centered headline, ≥ 1 structured block, GM |
| `chapter` | `02_chapter.svg` | between major divisions | 2-digit number, English chapter title, Korean label, summary line, page number; no GM |
| `end` | `04_ending.svg` | slide N | label, closing headline (e.g., 감사합니다.), accent line, contact line; no GM |

**Flow conventions:**
- Brochure flow: cover → agenda (p.2) → `01 ABOUT COMPANY` → `02 OUR SERVICE` → `03 OUR EXPERIENCE` → contact → closing.
- Chapter slides for decks ≥ 10 slides, every 3–6 body slides. Chapter titles in English caps (`OUR SERVICE`) with Korean label (`우리의 서비스`).
- Agenda (optional, slide 2) as a `structure` slide: 3–5 items, each a bold title + 2-line gray descriptor.
- A contact page (`CONTACT US`, light content shell with a filled contact card) may precede the closing band.

---

## 8. Chart & Table Treatment (Rhetorical Roles → Visual Implementation)

This preset honors the 9 rhetorical roles defined in `references/chart-rhetorical-roles.md`. Below is the preset-specific implementation layer.

### 8.1 Role → primary chart template

| `chart_strategy` | Primary | Alt |
|---|---|---|
| `growth-trend` | `bar_chart` (yearly columns, navy, data labels on top — p.20) | `line_chart` |
| `forecast` | `bar_chart` with projected years at `fill-opacity` 0.45 + "(예정)" label | `line_chart` dashed tail |
| `structural-break` | `line_chart` with vertical annotation rule | `bar_chart` before/after |
| `focus-comparison` | `horizontal_bar_chart` (ranked, focus bar 1.0, others 0.45 — p.20 right, p.21) | `bar_chart` |
| `distribution` | `horizontal_bar_chart` histogram | `data-table` |
| `quadrant` | `matrix_2x2` (navy axis labels) | `comparison-table` |
| `priority-matrix` | `navy-label-table` 3×3 with `accent-soft` cell for top priority | `matrix_2x2` |
| `split-segment` | `stacked_bar_chart` (100%, ladder) | `donut_chart` (≤ 5 segments) |
| `funnel` | `chevron-step-band` with decreasing counts | `funnel_chart` |
| `custom` | closest brochure pattern; describe in `chart_takeaway` | — |

### 8.2 Chart styling rules

- **Palette:** single-accent opacity ladder using `#012281`
- **Semantic exception:** `#059669` / `#E11D48` / `#D97706` only when color encodes data meaning

- **Legend:** no legend box; chart title uses a navy legend-dot (12px rounded square) + bold 18.4 title (`■ 연도별 수행 프로그램 수`, p.20).
- **Data labels** on every bar (15.2/400; navy on light bars, focus value bold).
- **Gridlines:** horizontal `#DFDFDF` 1px only; no axis box.
- **Axis labels:** `#1A1A1A` 15.2 for categories (brochure uses full-size category labels), `#666666` 12.8 for value ticks.
- **DS `BarChart`:** horizontal bars, value printed at the bar end, labels right-aligned to a hairline axis; `series=navy` for the primary measure, the second chart on the same slide uses navy at 0.45 (stand-in for `chart-blue`).
- **Forbidden:** drop shadows, 3D, gradient fills, glow, the literal `#58A6F6` (use ladder 0.45 instead).

### 8.3 Table styling rules

- **Label column** (navy-label-table): `#012281` fill, first row 1.0 and following rows `fill-opacity` 0.70, white 15.2/700 centered text, white 1px separators.
- **Header row** (comparison tables): `#F8F8F8` fill, label typography, `#595959`.
- **Value cells:** white, `#DFDFDF` 1px hairlines, centered 15.2 text; numerics right-aligned, tabular.
- **Recommended column/row:** `accent-soft #E0EDF3` background (counts as an accent event).
- **Verdict line:** one bold 15.2 sentence under the table.

### 8.4 Required adjacency: chart + takeaway

Every `data` family slide pairs its chart with a takeaway, preferably the **navy stat panel** on the left (p.20): hero number (Display-sm white) + 1-line context + up to 3 stat rows. When a panel would exceed the accent budget, use a `#F8F8F8` filled takeaway card instead (metric + trend + context). A chart without a takeaway fails R2 at plan time.

---

## 9. Icon System

### 9.1 Library lock

- **Default:** tabler-outline
- **Fallback:** tabler-filled
- **Forbidden:** other packs, emoji, unicode glyph icons, mixed packs.

### 9.2 Usage

```xml
<use data-icon="tabler-outline/<name>" x="..." y="..." width="..." height="..."
     fill="none" stroke="#012281" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
```

`finalize_svg.py` embeds the glyph. Icons are navy (`#012281`) line art on light slides (brochure p.8, p.9) and white inside navy satellites/panels. Navy icon strokes do not count as accent events.

### 9.3 Search before use

```bash
ls .claude/skills/slide/templates/icons/tabler-outline/ | grep <keyword>
```

### 9.4 Sizing

- Step / service icon: 32–40px, stroke 2.
- Card inline icon: 24px.
- Satellite icon (inside 64px navy disc with a 4px `#DFDFDF` ring — DS icon disc): 28px, white.
- Card icon (DS `InfoCard`): 24px line icon in `#1A1A1A` (DS `ink-strong`); process-column icons solid/line in navy.

### 9.5 Icon vs number badges

- Icons for service areas, steps, strengths (brochure default).
- Number badges only for ordered steps (`STEP 1–4`, `01–04`) and chapter numbers.
- A chevron row with STEP labels + an icon under each step is the standard mix.

### 9.6 Icon wrappers / decorations

- Bare line icons on light backgrounds.
- **Exception:** the `hub-and-satellite` pattern uses solid navy circles (64px) with white icons (p.7) — the only allowed wrapper, and the circles together count as one accent event.
- No colored badges, no gradient circles, no soft-tinted icon backgrounds.

---

## 10. Anti-Patterns (Reject at Plan Time)

| # | Anti-pattern | Detect via | Fix |
|---|---|---|---|
| A1 | Same family 3+ consecutive | `recommended_layout_family` streak | vary family or justify in `why_here` |
| A2 | Same dominant primitive 3+ consecutive | executor §0.1 #4 audit | rotate primitive (table → chevron → stat panel) |
| A3 | Same §5.2 variation 3+ times | per-page audit log | pick another variation |
| A4 | Chart without takeaway | `chart_strategy` set, `chart_takeaway` empty | add stat panel / takeaway card |
| A5 | Empty `evidence_sources` | array length 0 | add source id or `inference` |
| A6 | Multi-hue chart / brochure secondary blues as literals (`#486FB0`, `#58A6F6`) | off-palette hex | opacity ladder on `#012281` |
| A7 | Sky `#58CCFF` or navy band on a content slide | Rule T9 | sky is shell-only; content stays white |
| A8 | Multi-icon-pack mixing | icon names across packs | tabler-outline only |
| A9 | GM restating title | GM shares > 60% tokens with headline | rewrite as client impact |
| A10 | Casual / 해요체 voice in GM or notes | ending `~해요` / `~죠` | formal 합니다체 |
| A11 | Text-only body slide (headline + bullets) | no visual block | add table / step band / card stack |
| A12 | Left-aligned headline on content slide | headline x≠640 middle | centered headline per shell |
| A13 | Bordered cards | card `<rect>` with stroke | filled `#F8F8F8`, no border |
| A14 | 3+ accent events | navy block + accent text + accent-soft > 2 | merge into one navy block or drop one |
| A15 | Headline line break | `\n` / two `<text>` rows | shorten to one line |
| A16 | Decorative photo / stock image on content slide | `<image>` with decorative purpose | remove; photos only on narrative shells or as evidence |
| A17 | Gradient / shadow / glow | `linearGradient`, `filter` | flatten |
| A18 | Chevron row for parallel (non-sequential) items | step band without order | use filled-card-stack or icon grid |

---

## 11. Design-System Component Map (`Insightlearning-design-system` → slide-svg)

| DS component | Slide-svg realisation | Notes |
|---|---|---|
| `SlideTitle` | `03_content` shell header — label 24/300 + 136×6 bold segment over a 2px full-width navy rule | Never bold the label. `inverse` (white label, sky rule) only on narrative shells. |
| `SlideHeading` | shell `{{PAGE_TITLE}}` (29.6/800, centered) + optional lead at y=158 | Headline is a full-sentence claim ("고객의 니즈를 Business Impact로 전환합니다"); lead explains how. One line each. |
| `SectionOpener` | `02_chapter` shell | English uppercase title, Korean subtitle in navy, square number block. |
| `Cover` | `01_cover` shell | Navy field, diagonal cut + thin sky stripe, white logo top-left (x=56, y=48, h≈28). |
| `NavyPanel` | `navy-stat-panel-with-charts` / left-third navy anchor + InfoCard grid | Square by default; `rounded` (radius 28) for summary panels (TOTAL PROGRAM, PARTNERS). One per slide. |
| `InfoCard` | `filled-card-stack`, 2×3 grid right of a NavyPanel | tone `card #F8F8F8` (default) / `highlight #E0EDF3` (one item per row). DS `tile #EFEFEF` is folded into `#F8F8F8` (not a contract token). Radius 14, no border. |
| `StatCard` | `kpi-strip` | Three in a row, never one alone; real figures only. |
| `ProcessSteps` | `chevron-step-band` | Square interlocking chevrons "1 STEP…4 STEP"; detail columns beneath. `diagnostic` → accent-soft chevrons + navy outcome. |
| `DataTable` | `navy-label-table` | Navy header row; row-header column = navy @0.72 (steel stand-in); `#DFDFDF` hairlines; square. |
| `BarChart` | chart-design `horizontal_bar` with `focus` | Value at bar end; square key dot in title. |
| `Tag` | small `#F8F8F8` tile, radius 6, caption text | "업무관리 · 시간관리"; two-column grid, 12px gaps. |
| Logo | `assets/brand/insightlearning-logo-{white,color}.png` | Copy into `<project>/images/` and place via `<image href="../images/…">`. White on navy / cover / closing; color on white. Never recolor or redraw. |

**Shape language:** square (radius 0) for blocks, panels, chevrons, tables; radius 14 only on light cards; radius 6 on tags; radius 28 on the two summary panels; full discs for icons.

**Copy rules (DS Voice):** company speaks in ~합니다 / ~하겠습니다; client = 고객사 (never 여러분 / 당신); English for programme names and section titles; list items are noun phrases joined by " · " or " / " without sentence punctuation; contrast framing ("규모보다 깊이, 카탈로그보다 맞춤성"); real figures only; no emoji.

---

## Appendix — `slide-plan` quick reference

**Family vocabulary** (use one per slide): `structure` / `insight` / `breakdown` / `compare` / `data` / `process` / `visual`.

**Signature patterns:** `navy-label-table` (compare) · `filled-card-stack` (breakdown) · `chevron-step-band` (process) · `navy-stat-panel-with-charts` (data).

**Chart strategy vocabulary**: see `references/chart-rhetorical-roles.md`.

**Page family** (use one per slide): `title` / `chapter` / `body` / `end`.

**Slide role enum**: see `references/slide-role-enum.md`.

---

<!-- Authored 2026-10-07 by /theme-init from the 2026 Insightlearning company profile (26p). Hand-authored; preserved across re-runs. -->
