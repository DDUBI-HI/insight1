# Anti-Slop Reference (Theme): Active-Theme Literal Enforcement

Theme-specific anti-patterns for the **Insightlearning** theme (`insightlearning`). Structural rules that apply regardless of theme live in `anti-slop-core.md`.

> **Regenerate on theme change.** This file is rendered from `theme-active.json` each time `/theme-init` runs. Never hand-edit — edits will be overwritten.

---

## Rule T1: Exclusive Accent Hex

**Forbidden:** introducing any color beyond the locked palette. Especially, introducing a second "accent" hue alongside `#012281`.

**Allowed color values** — these are the only hex values permitted in generated SVG / CSS:

| Token | Value |
|-------|-------|
| `accent` | `#012281` |
| `accent-soft` | `#E0EDF3` |
| `accent-ink` | `#01185A` |
| `text` | `#000000` |
| `text-secondary` | `#595959` |
| `text-tertiary` | `#666666` |
| `bg` | `#FFFFFF` |
| `surface` | `#F8F8F8` |
| `surface-alt` | `#F2F2F2` |
| `border` | `#DFDFDF` |
| `border-strong` | `#B2B2B2` |
| `positive` | `#059669` (data contexts only) |
| `negative` | `#E11D48` (data contexts only) |
| `warning` | `#D97706` (data contexts only) |

**Why:** The slide-svg pipeline bakes tokens into DrawingML at export time, so runtime multi-theming is impossible. One file = one theme. Introducing off-palette colors guarantees a visual inconsistency that cannot be fixed post-export.

**Narrative-shell band colors** — additionally permitted, but ONLY on the narrative shells (`01_cover`, `02_chapter`, `04_ending`). NEVER on content slides:

| Token | Value | Scope |
|-------|-------|-------|
| `shell-bg` | `#012281` | narrative band fill (full-bleed) |
| `shell-text` | `#FFFFFF` | text on the band |
| `shell-text-secondary` | `#B3BDD9` | muted text on the band |
| `shell-accent` | `#58CCFF` | CTA / accent on the band |
| `shell-spectrum` | _(none)_ | decorative brand dots (narrative only) |

---

## Rule T2: Accent Rarity Budget (≤ 2 per slide)

**Forbidden:** painting multiple elements with `#012281` or `#E0EDF3` just to add visual variety.

**Allowed:** at most **two** accent "events" per content slide. An event is any of:
- Accent-colored text (`fill="#012281"`)
- Accent-soft filled container (`fill="#E0EDF3"`)
- Accent-stroked emphasis rule (`stroke="#012281"`)

**Why:** Accent is a pointer, not a palette. Multiple accents per slide cancel each other out and produce a "colorful SaaS dashboard" read instead of an editorial read.

---

## Rule T3: Font Chain Lock

**Forbidden:** any `<text>` element missing the full font chain, or using a different family.

**Correct:**
```xml
<text font-family="Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif" ...>
```

**Why:** If a viewer lacks the primary font, the chain degrades gracefully through Korean/Latin fallbacks. A missing or truncated chain causes system default rendering — typically a serif — which breaks the editorial tone instantly.

---

## Rule T4: Chart Palette — Single-Accent Opacity Ladder

**Forbidden:** multi-hue Chart.js palettes.

**Correct:** single accent with an opacity ladder. For `#012281`:

```js
backgroundColor: [
  'rgba(1, 34, 129, 0.85)',
  'rgba(1, 34, 129, 0.60)',
  'rgba(1, 34, 129, 0.40)',
  'rgba(1, 34, 129, 0.25)',
]
```

Semantic columns (growth vs. decline) may use `#059669` / `#E11D48` **only when the color encodes data meaning**.

**Why:** Chart.js cannot resolve CSS variables, so the palette must be literal. Multi-hue palettes re-introduce the "every series gets its own color" dashboard aesthetic that the single-accent discipline exists to prevent.

---

## Rule T5: Icon Library Lock

**Forbidden:** icons from packs other than `tabler-outline` (fallback: `tabler-filled`). Mixing multiple icon styles on one slide.

**Correct:** placeholder form processed by `finalize_svg.py`:

```xml
<use data-icon="tabler-outline/<name>"
     x="..." y="..." width="..." height="..."
     stroke="currentColor" stroke-width="2" />
```

**Why:** Mixing icon packs (outline + filled, line + glyph) is a dead giveaway of AI composition. A single family carries the visual through the whole deck.

---

## Rule T6: Voice & GM Tone Lock

**Forbidden phrases in GM and speaker notes:**
- 여러분
- 당신

**Required tone:**
- Register: Korean HRD consulting proposal / company profile, English for programme names, frameworks and section titles
- Point of view: first-person corporate — the company speaks as 인싸이트러닝 and calls the client 고객사
- Tone: consultative, confident, polite declarative (~합니다 / ~하겠습니다), contrast-framed

**GM composition hint:** One polite declarative sentence (~합니다) stating the business impact for 고객사; contrast framing ('A보다 B') welcome; real figures only; never a restatement of the headline.

**Why:** The GM line is the editorial contract between slide and audience. Tone drift is the fastest path to "AI-generated" smell; it's also the easiest to accidentally slip into via marketing-style filler.

---

## Rule T7: Radius Discipline

**Forbidden:** ad-hoc `rx="<arbitrary>"` values on `<rect>` elements.

**Allowed radius values** (in px):

| Name | Value | Usage |
|------|-------|-------|
| `xs` | 0 | chip, tight badge |
| `sm` | 5 | small callout, inline tag |
| `md` | 12 | default card |
| `lg` | 12 | hero card |
| `xl` | 25 | large container |
| `pill` | 9999 | fully rounded pill |

**Why:** Mixing radii within a deck (12px card next to 6px card next to 16px card) breaks the rhythm. The scale above is the only valid set.

---

## Rule T8: Stroke Width Discipline

**Allowed stroke widths:**

| Role | Value (px) | Usage |
|------|------------|-------|
| icon | 2 | line-art icons |
| divider | 1 | default structural dividers |
| emphasis | 2 | accent rule, highlight underline |

**Forbidden:** hairline strokes (<1px), display-weight strokes (>3px), or decorative dashed/dotted patterns.

**Why:** Stroke inconsistency is the other half of radius discipline. Together they set the deck's mechanical precision; drifting from these values is visible at a glance.

---

## Card Treatment Lock

The active theme's card treatment is **filled**. Apply it consistently across the whole deck.

**Forbidden:** mixing card treatments within one deck, or ignoring the active treatment.

**Filled lock:** card boxes use a `#F2F2F2` / `#F8F8F8` fill with **no** border. Do not add a 1px border on top of the fill.

**Why:** Card treatment is a structural identity signal. One file = one theme = one treatment; mixing hairline, filled, and borderless boxes reads as AI-assembled rather than designed.

---

## Rule T9: Narrative-Shell Band Scope

**Allowed:** the `shell-*` band fill and `shell-spectrum` hues appear ONLY on the narrative shells — `01_cover`, `02_chapter`, `04_ending`. These may render full-bleed on `#012281`, place `shell-text` / `shell-accent` text on the band, and show the brand spectrum as a decorative dot / bar row.

**Forbidden:**
- Any `shell-bg` band, `shell-spectrum` hue, or `shell-text` color on a **content** slide (`03_content` and every Executor-composed body slide). Content stays light: `#FFFFFF` / `#F8F8F8` backgrounds, `#000000` / `#595959` ink, single `#012281` accent.
- Using `shell-spectrum` as a data palette. It is decorative brand identity for narrative shells only — charts still use the single-accent opacity ladder (Rule T4).

**Budget:** spectrum dots are a single narrative-shell decoration and are NOT counted against the content accent budget (Rule T2); the spectrum row counts as one composition element and must not exceed the published `shell-spectrum` length.

**Why:** The light-mode relaxation is deliberately scoped. A dark hero on the cover / closing reads as branded and intentional; the same band on a dense content slide destroys the editorial, report-style legibility the deck depends on.

---

<!-- Rendered by render_anti_slop_theme.py from theme-active.json -->
