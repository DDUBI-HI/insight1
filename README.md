Insightlearning (인싸이트러닝) is an HRD consulting partner: "고객사 HRD 담당자의 외부 교육기획팀처럼 움직입니다." The visual system is navy-first, square, and quiet — one deep blue, one bright sky accent, generous white, and grayscale photography. Everything below is drawn from the 2026 company profile deck.

## Voice and content

- Write in Korean with English for programme names, frameworks and section titles: "Customized HRD for Business Performance", "AI × JOB", "Leadership Café-teria".
- Speak as the company, in polite declarative endings: "~합니다", "~하겠습니다". Use "고객사" for the client, never "you".
- Each slide makes one claim as a full sentence in `headline`: "고객의 니즈를 Business Impact로 전환합니다", "AI 도구 교육이 아니라, 'AI × JOB'으로 현업 성과를 만듭니다". The `lead` line under it explains how, in one sentence.
- Contrast framing is the house rhetoric: "규모보다 깊이, 카탈로그보다 맞춤성, 강사 공급보다 해결 설계".
- List items are noun phrases joined by " · " (middle dot) or " / ": "리더십 · 코칭 · 워크숍". No sentence punctuation inside lists.
- Section titles are English uppercase (ABOUT COMPANY, OUR SERVICE, OUR EXPERIENCE) with the Korean beneath in `navy`.
- Use real figures only (2014 설립, 665개 프로그램, 648건 세션, 19,614명). No emoji.

## Color

- `navy` is the brand. Use it for big fields (cover half, section blocks, feature panels), every chevron, table headers, primary chart bars and the title rule.
- `sky` is an accent that lives on `navy`: eyebrows, highlighted words ("Discovering Your **Purpose**"), panel labels, the rule under a panel title. Never set text in `sky` on white (1.8:1).
- `steel` labels table rows under a `navy` header; `chart-blue` is the second chart series only.
- Text: `ink` for headlines, `ink-strong` for numbers and card titles, `ink-body` for body, `ink-muted` for values in key–value lists, `ink-navy` for English card titles.
- Surfaces: `surface` for slides, `surface-card` for rounded cards, `surface-tile` for tags and timeline cards, `surface-alt` for strength-card headers, `tint-sky` for the single highlighted item in a row.
- `chart-blue` (2.6:1) and `ink-subtle` (2.5:1) are kept exactly from the deck and miss text contrast on white: use them for bars, large numerals or decoration, not for reading text. The white "02" on the `sky` block is likewise decorative.

## Typography

- Set everything in Pretendard (`sans`, variable font in `fonts/`). Headlines track tight (`-0.03em`), body slightly tight (`-0.02em`).
- Section openers use the heavy display face (`display`, Noto Sans KR Black via Google Fonts) in `display-xl`, uppercase.
- Hierarchy per slide: `slide-label` (Light, top-left) → `headline` (ExtraBold, centered) → `lead` → content in `card-title` / `body` / `small`. `eyebrow` is reserved for the cover line "COMPANY PROFILE 2026".
- Numbers carry weight: `stat` for key figures; years in timeline headers at `card-title-en` size in `navy`.

## Layout

- Slides are 16:9, designed on a 1440 × 810 canvas with `space-10` side margins.
- Every content slide: `SlideTitle` top-left, `SlideHeading` centered, then a two- to four-column grid with `space-4` gaps.
- A common composition is a `navy` panel in the left third with a 2 × 3 grid of `InfoCard`s on the right.
- Shapes are square: `radius-none` for blocks, panels, chevrons and tables. Rounding appears only on light cards (`radius-md`), small tags (`radius-sm`) and the two summary panels (`radius-lg`). Icons sit in `radius-full` discs.
- No shadows and no gradients. Separate with color fields and `line` hairlines.

## Imagery

- Photography is grayscale: glass towers shot from below, empty meeting rooms, hands over documents. On section and closing slides, wash it with `navy` (cover) or tint it blue (closing slide).
- The cover crops the photo with a diagonal edge and a thin `sky` stripe along the cut.

## Iconography

- Icons are simple solid or line pictograms (globe, chip, rising chart, person, handshake, magnifier, target, bulb) in `navy`, or white inside a `navy` disc with a light-gray ring.
- The deck's icon files are not included here; use a matching line set at 24px in `ink-strong` on cards, solid in `navy` for process columns.

## Logo

- Use `assets/Logos/insightlearning-logo-color.png` on white and light surfaces, `insightlearning-logo-white.png` on `navy` and on photos.
- Place it top-left on the cover and centered on the closing slide. Do not recolor, outline or redraw the swoosh mark.
