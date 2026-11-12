"""vkit.frame — the page shell shared by every slide.

  ┌───────────── white card (x 28–880) ─────────────┐  mint presenter zone (x ≥ 896)
  │ course label ───────────────────────────── 03   │
  │                 「 section 」                     │
  │          Title part 1 | Title part 2             │
  │                                                  │
  │              layout content (y 186–552)          │
  │                                                  │
  │        (✓)  governing message pill  (y 566–606)   │
  └──╲________________________________________╱────┘
  navy stage band (subtitle zone y ≥ 644)               raised right tab = presenter stage
"""
import prim
from prim import check_mark, circle, esc, fit, measure, path, plain, rect, text, two_tone, line, warn
from tokens import (BAND_PATH, BODY, CARD, CX, CONTENT_L, CONTENT_R, CONTENT_W, FONT, GM_BOX, GREEN, H,
                    HEADER_Y, MINT, MINT_BG, NAVY, SECTION_Y, T_LABEL, T_TITLE, TITLE_Y, W, WHITE)

HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n')


def background(band=True):
    o = rect(0, 0, W, H, MINT_BG)
    o += rect(CARD["x"], CARD["y"], CARD["w"], CARD["h"], WHITE, rx=CARD["rx"])
    if band:
        o += path(BAND_PATH, fill=NAVY)
    return o


def brand_mark(brand):
    """Small letter-spaced brand on the left tab of the stage band (outside the subtitle centre)."""
    return text(40, 690, brand, 12, 600, WHITE, ls=2.4, op=0.85) if brand else ""


def header(course, num):
    o = ""
    x = CONTENT_L
    if course:
        o += text(x, HEADER_Y, course, T_LABEL, 500, GREEN)
        x = x + measure(course, T_LABEL, 500) + 16
    o += line(x, HEADER_Y - 4.5, CONTENT_R - 44, HEADER_Y - 4.5, MINT, 1)
    if num is not None:
        o += text(CONTENT_R, HEADER_Y, f"{num:02d}", T_LABEL, 600, GREEN, anchor="end")
    return o


def section_label(s, y=SECTION_Y):
    return text(CX, y, prim.deco(s), 16, 500, GREEN, anchor="middle") if s else ""


def title(s, y=TITLE_Y, fs=T_TITLE, maxw=CONTENT_W - 20, c1=GREEN, c2=NAVY, anchor="middle", x=CX):
    """Two-tone title ('green part | navy part'). Shrinks to fit one line, never below 30px."""
    size = fs
    while measure(plain(s), size, 800) > maxw and size > 30:
        size -= 1
    if measure(plain(s), size, 800) > maxw:
        warn(f"title too long even at 30px: '{plain(s)}' — shorten to ≈ 20 characters")
    return two_tone(x, y, s, size, c1, c2, 800, anchor, ls=round(-0.03 * size, 2))


def gm_pill(s):
    """Governing message: navy pill + check, bottom of the content card (above the subtitle zone).
    verify_deck reads it through the project's .gm-band file."""
    x, y, w, h = GM_BOX
    (ln,), fs = fit(s, 17, w - 96, 1, 700, 15) if s else ([""], 17)
    o = rect(x, y, w, h, NAVY, rx=h / 2)
    o += check_mark(x + h / 2 + 2, y + h / 2, h / 2 - 6, WHITE, NAVY)
    o += text(x + w / 2 + 14, y + h / 2 + fs * 0.35, ln, fs, 700, WHITE, anchor="middle")
    return o


def page(body, *, course="", num=None, section=None, title_text=None, gm=None, brand="", band=True,
         title_y=TITLE_Y, title_fs=T_TITLE):
    o = [HEAD, background(band), header(course, num), section_label(section)]
    if title_text:
        o.append(title(title_text, y=title_y, fs=title_fs))
    o.append(body)
    if gm is not None:
        o.append(gm_pill(gm))
    o.append(brand_mark(brand))
    o.append("</svg>\n")
    return "".join(o)
