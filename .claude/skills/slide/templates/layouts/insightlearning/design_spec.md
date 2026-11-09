# Insightlearning Proposal Deck — Design Spec

> Prefilled defaults for the Insightlearning template pack (extracted from the 2026 Insightlearning company profile). Executor inherits these for every deck generated under the `slide` skill while this theme is active. Per-project values (title, page count, audience) are filled by the Strategist. Layout grammar SSOT: `DESIGN.md` in this folder.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | [Filled by Strategist] |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | [Filled by Strategist] |
| **Design Style** | Insightlearning — corporate B2B HRD consulting; white pages, deep navy accent, navy narrative bands |
| **Target Audience** | [Filled by Strategist — typically client HRD / HR managers and executives] |
| **Use Case** | Company profile, training proposal, program introduction, performance report |
| **Created Date** | [auto] |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | Left/right `56px`, bottom `64px` (GM reserve) |
| **Content Area** | x=56, y=168, w=1168, h=472 on content pages (below centered headline / optional lead, above GM) |

---

## III. Visual Theme — LOCKED

### Color Scheme

| Role | HEX | Token | Purpose |
| ---- | --- | ----- | ------- |
| **Background** | `#FFFFFF` | `--bg` | Page background |
| **Surface** | `#FFFFFF` | `--surface` | Table cells, containers |
| **Surface alt** | `#F8F8F8` | `--surface-alt` | Filled cards (no border) |
| **Text primary** | `#1A1A1A` | `--text` | Main text |
| **Text secondary** | `#595959` | `--text-secondary` | Descriptors, lead sentence, GM |
| **Text tertiary** | `#666666` | `--text-tertiary` | Captions, page numbers |
| **Border** | `#DFDFDF` | `--border` | Table hairlines, dividers |
| **Border strong** | `#C2C2C2` | `--border-strong` | Emphasis divider |
| **Accent** | `#012281` | `--accent` | Deep navy — structural blocks, rules, focus bars (max 2 events / slide) |
| **Accent soft** | `#E0EDF3` | `--accent-soft` | Recommended row / column highlight |
| **Accent ink** | `#1F375D` | `--accent-ink` | Darker navy (cover wedge, pressed) |
| **Positive / Negative / Warning** | `#059669` / `#E11D48` / `#D97706` | semantic | Data meaning only |

Narrative band (cover / chapter / ending only): `#012281` fill, `#FFFFFF` text, `#D2D6E3` muted text, `#58CCFF` sky accent.

### Color Rules

- Content slides stay white; navy appears as one structural block (label column, chevron row, stat panel) + at most one emphasis.
- Brochure secondary blues (`#486FB0`, `#58A6F6`) are expressed as `#012281` with `fill-opacity` 0.70 / 0.45 — never as literals.
- Sky `#58CCFF` never appears on a content slide.
- No gradients, no shadows, no glow.

---

## IV. Typography System

| Role | Font | Weight | Size (px) | Line-height | Letter-spacing |
| ---- | ---- | ------ | --------- | ----------- | -------------- |
| Display | Pretendard | 800 | 56 | 1.08 | -1.68 |
| Display-sm | Pretendard | 800 | 40 | 1.10 | -0.8 |
| Headline (centered) | Pretendard | 800 | 29.6 | 1.30 | -0.89 |
| Section label | Pretendard | 300 | 24 | 1.20 | -0.48 |
| Title | Pretendard | 600 | 18.4 | 1.30 | 0 |
| Body | Pretendard | 400 | 15.2 | 1.60 | 0 |
| Caption | Pretendard | 500 | 12.8 | 1.40 | 0 |
| Label (block eyebrow, uppercase) | Pretendard | 600 | 12.8 | 1.40 | 0.64 |

**Font chain** (every `<text>`): `Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif`

---

## V. Layout Principles

- **Header** — SlideTitle label top-left (24/300, y=62) + double navy rule (136×6 + 2px, y=72–78) + centered headline (y=128) + optional centered lead (y=158)
- **Body zone** — y=168 to y=640; prefer two blocks side by side (55% / 40%) or one wide block + one band
- **GM zone** — centered at y=680, `#595959`, 15.2/700
- **Cards** — filled `#F8F8F8`, radius 14, no border, padding 20, grid gap 16; blocks / panels / chevrons / tables square (radius 0)
- **Tables** — navy label column (`#012281`, rows at 0.70 opacity), white value cells, `#DFDFDF` hairlines
- **Signature patterns** — `navy-label-table`, `filled-card-stack`, `chevron-step-band`, `navy-stat-panel-with-charts` (see DESIGN.md §5.1)

---

## VI. Icon Usage

- `tabler-outline` only, 2px stroke, navy `#012281` on light, white inside navy shapes
- `<use data-icon="tabler-outline/<name>" x y width height fill="none" stroke="#012281" stroke-width="2"/>`; `finalize_svg.py` embeds the glyph
- Bare icons; the only wrapper is the navy satellite circle in `hub-and-satellite`
- Emoji / unicode icons forbidden

---

## VII. Visualization Reference List

[Filled by Strategist — chart colors use the `#012281` opacity ladder 1.0 / 0.70 / 0.45 / 0.25; legend-dot chart titles; data labels on bars.]

---

## VIII. Image Resource List

[Filled by Strategist. Photos only on narrative shells or as evidence; never decorative on content slides.]

**Brand logo (always available):** `templates/layouts/insightlearning/assets/brand/insightlearning-logo-white.png` (501×70, on navy: cover top-left, closing centered) and `insightlearning-logo-color.png` (859×168, on white). Copy into `<project>/images/` and reference with `<image href="../images/<file>">`. Never recolor or redraw.

---

## IX. Content Outline

[Filled by Strategist — per-page breakdown with page type, section label, centered headline, body plan, GM line.]

### GM (Governing Message) Rule

- One declarative sentence in formal Korean (…합니다 / …입니다 or noun ending), ≤ 35 chars ideal
- States the client-facing business impact — never restates the headline
- Rendered at y=680, centered, `#595959`, 15.2px, weight 700

Examples (voice calibration from the company profile):
- "리더십 교육을 조직의 실제 성과 행동으로 연결합니다"
- "6년간 665개 프로그램, 매년 110개 이상 운영합니다"
- "진단에서 행동 변화까지 하나의 흐름으로 설계합니다"

Title, chapter, and ending slides do NOT carry a GM.

---

## X. Speaker Notes Requirements

- Language: Korean (formal 합니다체)
- Markers: `[전환]`, `[멈춤]`, `[데이터]`, `[상호작용]`
- Voice: confident, consultative, company as subject ("인싸이트러닝은 …"); performance-oriented, no hype

---

## XI. Technical Constraints Reminder

- Canvas: 1280×720 only
- SVG constraints per `references/shared-standards.md` (banned: `<style>`, `class`, `<foreignObject>`, `mask`, `textPath`, animations, `rgba()`)
- Post-processing: `finalize_svg.py` — never substitute `cp`
- Export: `svg_to_pptx.py <project> -s final`

---

## Template Files

| File | Purpose |
| ---- | ------- |
| `01_cover.svg` | Navy hero cover with sky diagonal stripe |
| `02_chapter.svg` | Left navy panel + sky number box chapter divider |
| `03_content.svg` | Light content shell — section label, split navy rule, centered headline, GM |
| `04_ending.svg` | Navy closing with centered sky frame |

Executor composes freely inside x=56, y=168, w=1168, h=472 on `03_content.svg` while preserving the header (section label + rule + centered headline) and the GM line.
