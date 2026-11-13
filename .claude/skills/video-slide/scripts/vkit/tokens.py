"""vkit.tokens — design tokens for the video-lecture background deck (1280×720).

Single source of truth for colour, type and zone geometry. The same values are documented in
references/design-system.md and theme.json; change them here first, then update the docs.
"""

# ── colour (sampled from the reference template PDF) ─────────────────────────
NAVY = "#1D3E77"       # primary ink: titles part 2, stage band, GM pill, table header
GREEN = "#3EAE8D"      # primary accent: title part 1, section label, active items
TEAL = "#206C7A"       # secondary accent: 2nd/3rd card, sub-headings
MINT = "#80C4B0"       # light accent: alternate rows, 4th tier, connectors
MINT_BG = "#DBEEE8"    # outer background, soft panels
MINT_PALE = "#EEF7F4"  # very soft fill inside the card (tables, chips)
LAV = "#D9DEE8"        # neutral soft panel (the "before / not" side of a comparison)
WHITE = "#FFFFFF"
INK = "#1F2937"        # strongest body text (rare — table cells, card titles on white)
BODY = "#595959"       # body text
MUTED = "#8A94A6"      # captions, axis labels
LINE = "#D5DCE4"       # hairlines

# illustration-only colours (never for text or layout blocks)
SKIN = "#F5CBA7"
SKIN_2 = "#E9B48F"
SUN = "#F6C453"        # one warm pop colour so illustrations do not look flat

# Theme presets: hex → hex maps applied to every finished SVG (build_deck: spec `theme:`).
# Layout code always draws in the base "mint" tokens; a theme swaps them consistently,
# illustrations included. Keep new values unique so the swap never chains.
THEMES = {
    "mint": {},
    "indigo": {          # indigo + raspberry — calm blue with a warm human accent
        NAVY: "#2B3990", GREEN: "#D6456A", TEAL: "#4B5FC9", MINT: "#A7B2EC",
        MINT_BG: "#E6E9F7", MINT_PALE: "#F3F4FB", LAV: "#FBE4E6",
    },
    "coral": {           # deep teal + coral — warm and friendly
        NAVY: "#17485A", GREEN: "#E8674F", TEAL: "#2A8C99", MINT: "#F4B4A4",
        MINT_BG: "#FBEDE6", MINT_PALE: "#FDF6F2", LAV: "#E3EEF1",
    },
    "violet": {          # plum + violet — soft and modern
        NAVY: "#3B2A6E", GREEN: "#7B5CD6", TEAL: "#B0478F", MINT: "#C9B8F0",
        MINT_BG: "#EEE9FA", MINT_PALE: "#F7F4FD", LAV: "#FBE6F2",
    },
}


def themed(svg, theme):
    """Recolour a finished SVG with a theme preset (no-op for the base 'mint' theme)."""
    for a, b in THEMES.get(theme or "mint", {}).items():
        svg = svg.replace(a, b)
    return svg


def theme_palette(theme):
    m = THEMES.get(theme or "mint", {})
    return [m.get(c, c) for c in PALETTE]


PALETTE = [NAVY, GREEN, TEAL, MINT, MINT_BG, MINT_PALE, LAV, WHITE, INK, BODY, MUTED, LINE, SKIN, SKIN_2, SUN]

# series order for multi-item layouts (cards, pyramid tiers, hub circles …)
SERIES = [GREEN, TEAL, NAVY, MINT]
SERIES_SOFT = [MINT, GREEN, TEAL]          # 3-card "light → dark" ramp used by the template

FONT = "Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif"

# ── canvas + zones ───────────────────────────────────────────────────────────
W, H = 1280, 720
PRESENTER_X = 896          # right 30 % (x ≥ 896) is the presenter zone — background only
SUBTITLE_Y = 644           # y ≥ 644 is the subtitle zone (burned-in captions) — stage band only

CARD = dict(x=28, y=24, w=852, h=640, rx=22)      # white card (bottom hidden behind the band)
CX = 454                                           # horizontal centre of the content card
CONTENT_L, CONTENT_R = 64, 844                     # content safe area (inside the card)
CONTENT_W = CONTENT_R - CONTENT_L                  # 780
HEADER_Y = 58                                      # course label · hairline · page number
SECTION_Y = 96                                     # 「 section 」 label
TITLE_Y = 150                                      # title baseline (single line)
BODY_TOP, BODY_BOTTOM = 186, 552                   # free content area for layouts
GM_BOX = (104, 566, 700, 40)                       # x, y, w, h of the governing-message pill
GM_BAND = (560, 615)                               # y range verify_deck accepts for the GM (.gm-band)

# subtitle band: one straight navy bar across the full width (y 644–720) — burned-in captions sit on it
BAND_PATH = "M0,644 H1280 V720 H0 Z"

# ── type scale (px on the 1280×720 canvas; ≈ ×1.5 on a 1080p video) ────────
T_DISPLAY = 54      # cover / ending
T_TITLE = 38        # slide title (auto-shrinks to 30)
T_STATEMENT = 40    # statement layout
T_H2 = 22           # card / item title
T_BODY = 17         # body text — never below 15 on a video slide
T_SMALL = 15        # captions, table cells
T_LABEL = 13        # header label, page number
T_BIG = 50          # stat numbers
