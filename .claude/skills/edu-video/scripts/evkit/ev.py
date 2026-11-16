"""evkit.ev — edu-video design system: tokens, text fitting, shells and 18 layouts.

Canvas 1280×720 (PPT 16:9). The RIGHT 30% (x ≥ 896) is the instructor stage and stays empty;
the BOTTOM band (y ≥ 644) is the caption safe zone and stays empty. Everything is sized for
low-vision learners: no text below 28px (21pt), body 32px (24pt). Canonical rules:
.claude/skills/edu-video/references/design-system.md
"""
import os
import re

import illust

# ───────────────────────────── tokens ─────────────────────────────
W, H = 1280, 720
X0, X1 = 64, 848                 # content zone (left 70% minus gutter)
CW = X1 - X0                     # 784
CX = (X0 + X1) // 2              # 456 — optical centre of the content zone
STAGE_X = 896                    # instructor stage: x 896–1280 (30%)
SAFE_X = 872                     # nothing may cross this (24px gutter before the stage)
BODY_TOP, BODY_BOT = 196, 552
KEY_Y, KEY_H = 568, 60           # key-message strip
CAPTION_Y = 644                  # caption safe zone: y 644–720

NAVY, SOFT, INK, SKY = "#012281", "#E0EDF3", "#1F375D", "#58CCFF"
TEXT, MUTED, CARD, LINE, LINE2, WHITE, SHELL2 = "#1A1A1A", "#595959", "#F8F8F8", "#DFDFDF", "#C2C2C2", "#FFFFFF", "#D2D6E3"

F = "Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif"
FS = {"display": 64, "h1": 44, "h2": 36, "body": 32, "key": 30, "min": 28}
MIN_FS = 28
LH = 1.45                        # body line-height

OUT = None                       # set by build: output/<project>/svg_output
STAGE = "tint"                   # tint | plain
LOGO = True
WIDTH = 2                        # filename index digits (3 when the deck has 100+ slides — keeps sort order)


class FitError(Exception):
    pass


# ───────────────────────────── text ─────────────────────────────

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cw(c, fs):
    o = ord(c)
    if c in "·":
        return fs * 0.3
    if o >= 0x1100:                       # Hangul / CJK — Pretendard 0.864em, +margin for Malgun fallback
        return fs * (0.42 if c in "「」『』‘’“”" else 0.92)
    if c == " ":
        return fs * 0.26
    if c in ".,:;!|'`":
        return fs * 0.3
    if c in "()[]{}-–/\"":
        return fs * 0.4
    if c.isdigit():
        return fs * 0.6
    if c.isupper():
        return fs * 0.68
    return fs * 0.56


def text_w(s, fs, bold=False):
    s = s.replace("**", "")
    return sum(cw(c, fs) for c in s) * (1.03 if bold else 1.0)


def _chars(s):
    """'a **b** c' → [(char, emph)]"""
    out, emph = [], False
    for i, part in enumerate(s.split("**")):
        out += [(c, i % 2 == 1) for c in part]
    return out


def wrap(s, fs, maxw, bold=False, balance=True):
    """Word wrap by estimated pixel width; keeps **emphasis** across breaks.
    Explicit breaks: '\\n' or ' | '. balance=True evens out line lengths (no one-word orphan lines)."""
    out = []
    for para in re.split(r"\n| \| ", str(s)):
        lines = _greedy(para, fs, maxw, bold)
        if balance and len(lines) > 1:
            longest = max(sum(cw(c, fs) for c, _ in wd) * (1.03 if bold else 1) for wd in _words(para))
            lo, hi = min(maxw, max(maxw * 0.35, longest)), maxw
            for _ in range(14):
                mid = (lo + hi) / 2
                if len(_greedy(para, fs, mid, bold)) <= len(lines):
                    hi = mid
                else:
                    lo = mid
            lines = _greedy(para, fs, hi, bold)
        out += lines
    return out


def _words(para):
    """Split into words; a standalone separator ('·', ',', '/') sticks to the previous word
    so no line starts with it."""
    words, cur = [], []
    for ch in _chars(para):
        if ch[0] == " ":
            if cur:
                words.append(cur)
            cur = []
        else:
            cur.append(ch)
    if cur:
        words.append(cur)
    out = []
    for wd in words:
        if out and "".join(c for c, _ in wd) in ("·", ",", "/", "-", "–"):
            out[-1] = out[-1] + [(" ", False)] + wd
        else:
            out.append(wd)
    return out


def _greedy(para, fs, maxw, bold):
    lines = []
    if True:
        words = _words(para)
        line, lw = [], 0.0
        sp = cw(" ", fs)
        for wd in words:
            ww = sum(cw(c, fs) for c, _ in wd) * (1.03 if bold else 1)
            if line and lw + sp + ww > maxw:
                lines.append(line)
                line, lw = [], 0.0
            if ww > maxw:                 # long word → break, preferably right after a '·'
                if line:
                    lines.append(line)
                    line, lw = [], 0.0
                for ch in wd:
                    c_w = cw(ch[0], fs)
                    if line and lw + c_w > maxw:
                        cut = max((k for k, (c, _) in enumerate(line) if c == "·"), default=-1)
                        if 0 <= cut < len(line) - 1:
                            rest = line[cut + 1:]
                            lines.append(line[:cut + 1])
                            line, lw = rest, sum(cw(c, fs) for c, _ in rest)
                        else:
                            lines.append(line)
                            line, lw = [], 0.0
                    line.append(ch)
                    lw += c_w
                continue
            if line:
                line.append((" ", line[-1][1] and wd[0][1]))
                lw += sp
            line += wd
            lw += ww
        if line:
            lines.append(line)
    out = []
    for ln_ in lines:
        s2, cur = "", False
        for c, e in ln_:
            if e != cur:
                s2 += "**"
                cur = e
            s2 += c
        if cur:
            s2 += "**"
        out.append(s2)
    return out


def t(x, y, s, fs=32, fw=400, fill=TEXT, anchor=None, emph=NAVY, ls=None):
    """<text> with **emphasis** runs (bold + accent colour — never colour alone)."""
    if fs < MIN_FS:
        raise FitError(f"font-size {fs}px < {MIN_FS}px minimum: {s!r}")
    a = f' text-anchor="{anchor}"' if anchor else ''
    l_ = f' letter-spacing="{ls}"' if ls is not None else ''
    parts = s.split("**")
    body = ""
    for i, p in enumerate(parts):
        if not p:
            continue
        body += f'<tspan font-weight="700" fill="{emph}">{esc(p)}</tspan>' if i % 2 else esc(p)
    return (f'  <text x="{round(x, 1)}" y="{round(y, 1)}" font-family="{F}" font-size="{fs}" '
            f'font-weight="{fw}"{l_}{a} fill="{fill}">{body}</text>\n')


def para(x, y, lines, fs, fw=400, fill=TEXT, anchor=None, lh=LH, emph=NAVY):
    """Multiline text; y = first baseline. Returns (svg, last_baseline)."""
    o = ""
    for i, s in enumerate(lines):
        o += t(x, y + i * fs * lh, s, fs, fw, fill, anchor, emph)
    return o, y + (len(lines) - 1) * fs * lh


def block_h(n, fs, lh=LH):
    """Visual height of n lines (cap-top of first to descender of last)."""
    return fs * 0.78 + (n - 1) * fs * lh + fs * 0.22 if n else 0


# ───────────────────────────── primitives ─────────────────────────────

def r(x, y, w, h, fill=CARD, rx=None, stroke=None, sw=2, op=None):
    a = f' rx="{rx}"' if rx else ''
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    o = f' fill-opacity="{op}"' if op is not None else ''
    return f'  <rect x="{round(x, 1)}" y="{round(y, 1)}" width="{round(w, 1)}" height="{round(h, 1)}"{a} fill="{fill}"{o}{s}/>\n'


def circ(cx, cy, rr, fill=NAVY, stroke=None, sw=2):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    return f'  <circle cx="{round(cx, 1)}" cy="{round(cy, 1)}" r="{rr}" fill="{fill}"{s}/>\n'


def ln(x1, y1, x2, y2, c=LINE, w=2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'  <line x1="{round(x1, 1)}" y1="{round(y1, 1)}" x2="{round(x2, 1)}" y2="{round(y2, 1)}" '
            f'stroke="{c}" stroke-width="{w}" stroke-linecap="round"{d}/>\n')


def path(d, fill="none", stroke=NAVY, sw=3):
    return (f'  <path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>\n')


ICON_DIR = None


def icon(name, x, y, s=40, c=NAVY):
    """Tabler outline icon (2px line-art, repo rule). finalize_svg embeds it."""
    if ICON_DIR and not os.path.exists(os.path.join(ICON_DIR, name + ".svg")):
        raise FitError(f"unknown tabler-outline icon {name!r} (assets/icons/tabler-outline/)")
    return (f'  <use data-icon="tabler-outline/{name}" x="{round(x, 1)}" y="{round(y, 1)}" width="{s}" height="{s}" '
            f'fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>\n')


def check_mark(cx, cy, k=1.0, c=WHITE, sw=4):
    return path(f"M{cx - 11 * k} {cy} L{cx - 3 * k} {cy + 8 * k} L{cx + 12 * k} {cy - 9 * k}", stroke=c, sw=sw)


def o_mark(cx, cy, rr, c=NAVY, sw=12):
    return circ(cx, cy, rr, fill="none", stroke=c, sw=sw)


def x_mark(cx, cy, rr, c=MUTED, sw=12):
    return ln(cx - rr, cy - rr, cx + rr, cy + rr, c, sw) + ln(cx + rr, cy - rr, cx - rr, cy + rr, c, sw)


def pill(x, y, s, fs=28, fill=SOFT, color=NAVY, stroke=None, h=None):
    h = h or round(fs * 1.6)
    w = text_w(s, fs, True) + fs * 1.4
    return r(x, y, w, h, fill, h / 2, stroke) + t(x + fs * 0.7, y + h / 2 + fs * 0.36, s, fs, 700, color), w


CUR = {}   # slide being built — lets `image:` take the illustration slot


def ill(name, x, y, size, dark=False):
    if x + size > SAFE_X + 0.5:
        raise FitError(f"illustration {name!r} crosses into the instructor stage (x+size={x + size} > {SAFE_X})")
    if CUR.get("image") and CUR.get("layout") not in ("screen", "photo"):
        return _img(CUR["image"], x, y, size, size, CUR.get("fit", "slice"))
    return illust.draw(name, x, y, size, dark)


# ───────────────────────────── shells ─────────────────────────────

def _svg(parts):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            + "".join(parts) + '</svg>\n')


# Colour themes — one accent per deck. Pages are drawn in the navy base palette and remapped here,
# so layouts, icons and illustrations all follow. Every theme keeps the contrast rules (design-system.md §5):
# accent on white ≥ 10:1, accent on soft ≥ 8:1, shell text (sky / shell2) on accent ≥ 7:1.
PALETTES = {
    "navy":   {"accent": "#012281", "soft": "#E0EDF3", "ink": "#1F375D", "sky": "#58CCFF", "shell2": "#D2D6E3"},
    "teal":   {"accent": "#004A4F", "soft": "#DCEFEE", "ink": "#11605F", "sky": "#8CEBDF", "shell2": "#D3EBE9"},
    "purple": {"accent": "#45277F", "soft": "#ECE6F6", "ink": "#5A3E97", "sky": "#D4C2FF", "shell2": "#DCD3EF"},
    "green":  {"accent": "#164A2A", "soft": "#E2F0E6", "ink": "#265F3B", "sky": "#A6EDB8", "shell2": "#D5EADB"},
    "wine":   {"accent": "#701735", "soft": "#F6E4E9", "ink": "#872B49", "sky": "#FFC2D3", "shell2": "#EED3DB"},
}
PALETTE = "navy"


def palette_map():
    base, cur = PALETTES["navy"], PALETTES[PALETTE]
    return {base[k]: cur[k] for k in base if base[k] != cur[k]}


def _write(fname, svg):
    for a, b in palette_map().items():
        svg = svg.replace(a, b).replace(a.lower(), b)
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
        f.write(svg)


def stage_rect():
    return r(STAGE_X, 0, W - STAGE_X, H, SOFT).replace("<rect ", '<rect id="stage" ') if STAGE == "tint" else ""


def header(label, title, cite=None):
    o, lw = "", 0
    if label:
        p_, lw = pill(X0, 40, label)
        o += p_
    if cite:                      # source citation, right-aligned on the label row (28px, muted)
        cw_ = text_w("출처 " + cite, FS["min"])
        if lw + 24 + cw_ > CW:
            raise FitError(f"cite too long for the label row (≈{int((CW - lw - 24) / (FS['min'] * 0.92))} chars): {cite!r}")
        o += t(X1, 73, f"출처 {cite}", FS["min"], 400, MUTED, anchor="end")
    if text_w(title, FS["h1"], True) > CW:
        raise FitError(f"title too long for one line at 44px (≈17 Hangul chars): {title!r}")
    o += t(X0, 140, title, FS["h1"], 700, TEXT)
    o += ln(X0, 168, X1, 168, LINE, 2) + r(X0, 166, 88, 4, NAVY)
    return o


KEY_REQUIRED = True   # deck option `key: source_only` turns this off (key only where the source has the sentence)


def key_lines(key):
    """Key text as 1–2 lines (2 only when the source sentence is too long for one)."""
    if not key:
        return []
    if text_w(key, FS["key"], True) <= CW - 120:
        return [key]
    ln2 = wrap(key, FS["min"], CW - 64, True)
    if len(ln2) > 2:
        raise FitError(f"key too long even on two lines: {key!r}")
    return ln2


def key_strip(key):
    if not key:
        if KEY_REQUIRED:
            raise FitError("content slide needs `key` (one-line takeaway / governing message)")
        return ""
    lines = key_lines(key)
    if len(lines) == 1:
        tw = text_w(key, FS["key"], True)
        o = r(X0, KEY_Y, CW, KEY_H, SOFT, 16)
        ix = CX - tw / 2 - 48
        if ix >= X0 + 12:
            o += icon("bulb", ix, KEY_Y + 13, 34)
            o += t(CX + 20, KEY_Y + 40, key, FS["key"], 700, NAVY, anchor="middle")
        else:
            o += t(CX, KEY_Y + 40, key, FS["key"], 700, NAVY, anchor="middle")
        return o
    top = KEY_Y + KEY_H - 84
    o = r(X0, top, CW, 84, SOFT, 16)
    o += t(CX, top + 35, lines[0], FS["min"], 700, NAVY, anchor="middle")
    o += t(CX, top + 71, lines[1], FS["min"], 700, NAVY, anchor="middle")
    return o


def content_page(fname, s, body):
    parts = ['  <rect width="1280" height="720" fill="#FFFFFF"/>\n', stage_rect(),
             header(s.get("label"), s["title"], s.get("cite")), body, key_strip(s.get("key"))]
    _write(fname, _svg(parts))


def navy_page(fname, body):
    parts = ['  <rect width="1280" height="720" fill="#012281"/>\n', body]
    _write(fname, _svg(parts))


def logo(x, y, anchor="start"):
    if not LOGO:
        return ""
    w = 200
    x = x - w / 2 if anchor == "middle" else x
    return (f'  <image href="../images/insightlearning-logo-white.png" x="{x}" y="{y}" width="{w}" height="28" '
            f'preserveAspectRatio="xMinYMid meet"/>\n')


def vcenter(h, top=None, bot=None):
    top = BODY_TOP if top is None else top
    bot = BODY_BOT if bot is None else bot
    if h > bot - top + 0.5:
        raise FitError(f"content block {round(h)}px taller than the body area ({bot - top}px) — shorten or split the slide")
    return top + (bot - top - h) / 2


# ───────────────────────────── layouts ─────────────────────────────

def L_cover(s):
    o = logo(X0, 64)
    o += pill(X0, 140, s.get("eyebrow", "교육 영상"), fill=NAVY, color=SKY, stroke=SKY)[0]
    title = s["title"] if isinstance(s["title"], list) else wrap(s["title"], FS["display"], 720, True)
    if len(title) > 2:
        raise FitError(f"cover title wraps to {len(title)} lines (max 2, ≈11 chars/line): {s['title']!r}")
    for i, tl in enumerate(title):
        if text_w(tl, FS["display"], True) > 760:
            raise FitError(f"cover title line too long: {tl!r}")
        o += t(X0, 278 + i * 84, tl, FS["display"], 700, WHITE, emph=SKY)
    y = 278 + (len(title) - 1) * 84 + 76
    sub = wrap(s.get("sub", ""), FS["body"], 540) if s.get("sub") else []
    p_, y2 = para(X0, y, sub, FS["body"], 400, SHELL2)
    o += p_
    if s.get("meta"):
        o += t(X0, max(y2 + 64, 520), s["meta"], FS["min"], 400, SHELL2)
    o += ill(s.get("illust", "graduate"), 616, 380, 232, dark=True)
    return o


def L_chapter(s):
    o = t(X0, 214, s.get("eyebrow", "CHAPTER"), FS["min"], 700, SKY, ls=2)
    o += t(X0, 336, f"{int(s.get('number') or s.get(False) or s.get('_auto_no', 1)):02d}", 128, 700, WHITE)
    cfs = 56
    lines = wrap(s["title"], cfs, 520, True)
    if len(lines) > 2 or any(text_w(l_, cfs, True) > 540 for l_ in lines):
        cfs = 46
        lines = wrap(s["title"], cfs, 540, True)
    if len(lines) > 2 or any(text_w(l_, cfs, True) > 560 for l_ in lines):
        raise FitError(f"chapter title too long (2 lines): {s['title']!r}")
    p_, y = para(X0, 428, lines, cfs, 700, WHITE, lh=1.25, emph=SKY)
    o += p_
    if s.get("sub"):
        sub = wrap(s["sub"], FS["key"], 520)
        if len(sub) > 2:
            raise FitError(f"chapter sub too long: {s['sub']!r}")
        o += para(X0, y + 64, sub, FS["key"], 400, SHELL2)[0]
    o += ill(s.get("illust", "book"), 600, 210, 248, dark=True)
    return o


def L_ending(s):
    o = ill(s.get("illust", "trophy"), CX - 110, 104, 220, dark=True)
    o += t(CX, 410, s.get("title", "수고하셨습니다"), FS["display"], 700, WHITE, anchor="middle")
    if s.get("sub"):
        for i, sl in enumerate(wrap(s["sub"], FS["body"], 720)[:2]):
            o += t(CX, 476 + i * 46, sl, FS["body"], 400, SHELL2, anchor="middle")
    o += logo(CX, 574, "middle")
    return o


def L_agenda(s):
    items = s["items"]
    if not 2 <= len(items) <= 6:
        raise FitError("agenda takes 2–6 items")
    il = s.get("illust")
    maxw = (560 if il else CW) - 72
    rh = min(80, (BODY_BOT - BODY_TOP) / len(items))
    top = vcenter(rh * len(items))
    cur = s.get("current")
    o = ""
    for i, it in enumerate(items):
        y = top + i * rh
        if text_w(it, FS["body"], True) > maxw:
            raise FitError(f"agenda item too long for one line: {it!r}")
        on = cur == i + 1
        if on:
            o += r(X0 - 12, y + 6, (560 if il else CW) + 12, rh - 12, SOFT, (rh - 12) / 2)
        o += circ(X0 + 28, y + rh / 2, 26, NAVY if (cur is None or on) else WHITE, None if (cur is None or on) else NAVY, 3)
        o += t(X0 + 28, y + rh / 2 + 10, f"{i + 1}", FS["min"], 700, WHITE if (cur is None or on) else NAVY, anchor="middle")
        o += t(X0 + 76, y + rh / 2 + 11, it, FS["body"], 700 if (cur is None or on) else 400, TEXT if (cur is None or on) else MUTED)
        if i < len(items) - 1 and cur is None:
            o += ln(X0 + 76, y + rh, X0 + (560 if il else CW), y + rh, LINE, 2)
    if il:
        o += ill(il, 616, vcenter(232), 232)
    return o


def L_concept(s):
    """Statement + emphasis + illustration (the classic '정의' page)."""
    il = s.get("illust", "question")
    maxw = 500 if il else CW
    lines = []
    for ln_ in (s.get("lines") or []):
        lines += wrap(ln_, FS["h2"], maxw)
    em = wrap(s["emphasis"], FS["h1"], maxw, True) if s.get("emphasis") else []
    h = block_h(len(lines), FS["h2"]) + (28 + block_h(len(em), FS["h1"], 1.3) if em else 0)
    top = vcenter(h)
    o = ""
    y = top + FS["h2"] * 0.78
    if lines:
        p_, y = para(X0, y, lines, FS["h2"], 400, TEXT)
        o += p_
        y += FS["h2"] * 0.22 + 28 + FS["h1"] * 0.78
    else:
        y = top + FS["h1"] * 0.78
    for i, el in enumerate(em):
        yy = y + i * FS["h1"] * 1.3
        o += r(X0 - 4, yy - 12, text_w(el, FS["h1"], True) + 8, 20, SOFT)
        o += t(X0, yy, el, FS["h1"], 700, NAVY)
    if il:
        o += ill(il, 596, vcenter(252), 252)
    return o


def _rows(items, X, maxw, with_icon=True, numbered=False, check=False):
    """Icon/number rows: items [{icon?, text, sub?}] or [str]. Returns (svg, total_h) laid out from y=0."""
    rows = []
    for it in items:
        it = {"text": it} if isinstance(it, str) else it
        tl = wrap(it["text"], FS["body"], maxw, True)
        sl = wrap(it["sub"], FS["min"], maxw) if it.get("sub") else []
        hh = max(72, block_h(len(tl), FS["body"], 1.35) + (12 + block_h(len(sl), FS["min"], 1.35) if sl else 0))
        rows.append((it, tl, sl, hh))
    gap = 24 if len(rows) <= 3 else 14
    total = sum(rw[3] for rw in rows) + gap * (len(rows) - 1)
    return rows, total, gap


def L_bullets(s):
    items = s["items"]
    if not 1 <= len(items) <= 4:
        raise FitError("bullets takes 1–4 items")
    il = s.get("illust")
    right = 568 if il else X1
    TX = X0 + 96
    rows, total, gap = _rows(items, TX, right - TX)
    lead = wrap(s["lead"], FS["h2"], right - X0, True) if s.get("lead") else []
    lh_ = block_h(len(lead), FS["h2"], 1.3) + 32 if lead else 0
    y = vcenter(total + lh_)
    o = ""
    if lead:
        o += para(X0, y + FS["h2"] * 0.78, lead, FS["h2"], 700, NAVY, lh=1.3)[0]
        y += lh_
    for i, (it, tl, sl, hh) in enumerate(rows):
        o += r(X0, y, 72, 72, SOFT, 20)
        if it.get("icon"):
            o += icon(it["icon"], X0 + 16, y + 16, 40)
        else:
            o += t(X0 + 36, y + 47, f"{i + int(s.get('start', 1))}", FS["body"], 700, NAVY, anchor="middle")
        th = block_h(len(tl), FS["body"], 1.35) + (12 + block_h(len(sl), FS["min"], 1.35) if sl else 0)
        ty = y + max(0, (72 - th) / 2) + FS["body"] * 0.78
        p_, yl = para(TX, ty, tl, FS["body"], 700, TEXT, lh=1.35)
        o += p_
        if sl:
            o += para(TX, yl + FS["body"] * 0.22 + 12 + FS["min"] * 0.78, sl, FS["min"], 400, MUTED, lh=1.35)[0]
        y += hh + gap
    if il:
        o += ill(il, 600, vcenter(248), 248)
    return o


def L_summary(s):
    items = s["items"]
    if not 2 <= len(items) <= 4:
        raise FitError("summary takes 2–4 items")
    il = s.get("illust", "trophy")
    right = 568 if il else X1
    TX = X0 + 80
    rows, total, gap = _rows(items, TX, right - TX)
    y = vcenter(total)
    o = ""
    for it, tl, sl, hh in rows:
        th = block_h(len(tl), FS["body"], 1.35) + (12 + block_h(len(sl), FS["min"], 1.35) if sl else 0)
        cy = y + max(0, (72 - th) / 2) + 22
        o += circ(X0 + 26, cy, 26, NAVY) + check_mark(X0 + 26, cy, 1.0)
        ty = y + max(0, (72 - th) / 2) + FS["body"] * 0.78
        p_, yl = para(TX, ty, tl, FS["body"], 700, TEXT, lh=1.35)
        o += p_
        if sl:
            o += para(TX, yl + FS["body"] * 0.22 + 12 + FS["min"] * 0.78, sl, FS["min"], 400, MUTED, lh=1.35)[0]
        y += hh + gap
    if il:
        o += ill(il, 600, vcenter(248), 248)
    return o


def L_cards(s):
    items = s["items"]
    n = len(items)
    if not 2 <= n <= 3:
        raise FitError("cards takes 2–3 items (use bullets for more)")
    gap = 24
    w = (CW - gap * (n - 1)) / n
    hl = s.get("highlight")

    def measure(pad, tile, g1, g2):
        out = []
        for it in items:
            tl = wrap(it["title"], FS["body"], w - 2 * pad, True)
            bl = wrap(it.get("text", ""), FS["min"], w - 2 * pad) if it.get("text") else []
            hh = pad + tile + g1 + block_h(len(tl), FS["body"], 1.3) + (g2 + block_h(len(bl), FS["min"], 1.4) if bl else 0) + pad
            out.append((tl, bl, hh))
        return out
    pad, tile, g1, g2 = 28, 72, 28, 20
    meas = measure(pad, tile, g1, g2)
    if max(m[2] for m in meas) > BODY_BOT - BODY_TOP:      # compact spacing when tight
        pad, tile, g1, g2 = 22, 56, 18, 14
        meas = measure(pad, tile, g1, g2)
    ch = max(280 if tile == 72 else 0, max(m[2] for m in meas))
    top = vcenter(ch)
    o = ""
    for k, (it, (tl, bl, _)) in enumerate(zip(items, meas)):
        x = X0 + k * (w + gap)
        on = hl == k + 1
        o += r(x, top, w, ch, SOFT if on else CARD, 24)
        o += r(x + pad, top + pad, tile, tile, NAVY if on else WHITE, 20 if tile == 72 else 16)
        isz = 40 if tile == 72 else 32
        o += icon(it.get("icon", "point"), x + pad + (tile - isz) / 2, top + pad + (tile - isz) / 2, isz, WHITE if on else NAVY)
        p_, y = para(x + pad, top + pad + tile + g1 + FS["body"] * 0.78, tl, FS["body"], 700, NAVY if on else TEXT, lh=1.3)
        o += p_
        if bl:
            o += para(x + pad, y + FS["body"] * 0.22 + g2 + FS["min"] * 0.78, bl, FS["min"], 400, TEXT if on else MUTED, lh=1.4)[0]
    return o


def L_compare(s):
    sides = (s["left"], s["right"])
    gap, pad, fs = 24, 28, FS["body"]
    w = (CW - gap) / 2
    meas = []
    for side in sides:
        rows = [wrap(it, fs, w - 2 * pad - 24) for it in side["items"]]
        hh = 76 + 32 + sum(block_h(len(rw), fs, 1.35) for rw in rows) + 20 * (len(rows) - 1) + 36
        meas.append((rows, hh))
    ch = max(240, max(m[1] for m in meas))
    top = vcenter(ch)
    o = ""
    for k, (side, (rows, _)) in enumerate(zip(sides, meas)):
        x = X0 + k * (w + gap)
        good = str(side.get("mark", "O" if k == 0 else "X")).upper() == "O"
        hc = NAVY if good else MUTED
        o += r(x, top, w, ch, CARD, 20) + r(x, top, w, 76, hc, 20) + r(x, top + 40, w, 36, hc)
        o += circ(x + 50, top + 38, 22, WHITE)
        if good:
            o += circ(x + 50, top + 38, 11, "none", NAVY, 4.5)
        else:
            o += ln(x + 42, top + 30, x + 58, top + 46, MUTED, 4.5) + ln(x + 58, top + 30, x + 42, top + 46, MUTED, 4.5)
        if text_w(side["title"], fs, True) <= w - 112:
            o += t(x + 88, top + 49, side["title"], fs, 700, WHITE)
        elif text_w(side["title"], FS["min"], True) <= w - 104:
            o += t(x + 88, top + 48, side["title"], FS["min"], 700, WHITE)
        else:
            tl2 = wrap(side["title"], FS["min"], w - 104, True)
            if len(tl2) > 2:
                raise FitError(f"compare title too long: {side['title']!r}")
            o += t(x + 88, top + 33, tl2[0], FS["min"], 700, WHITE) + t(x + 88, top + 65, tl2[1], FS["min"], 700, WHITE)
        y = top + 76 + 32
        for rw in rows:
            base = y + fs * 0.78
            o += circ(x + pad + 6, base - fs * 0.33, 6, hc)
            o += para(x + pad + 24, base, rw, fs, 400, TEXT, lh=1.35)[0]
            y += block_h(len(rw), fs, 1.35) + 20
    return o


def L_steps(s):
    items = s["items"]
    n = len(items)
    if not 2 <= n <= 5:
        raise FitError("steps takes 2–5 items")
    cw_ = CW / n
    cy = BODY_TOP + 54
    o = ln(X0 + cw_ / 2, cy, X0 + cw_ * (n - 0.5), cy, NAVY, 3, dash="2 10")
    for i, it in enumerate(items):
        it = {"title": it} if isinstance(it, str) else it
        cx = X0 + cw_ * (i + 0.5)
        o += circ(cx, cy, 44, NAVY)
        if it.get("icon"):
            o += icon(it["icon"], cx - 22, cy - 22, 44, WHITE)
        else:
            o += t(cx, cy + 12, f"{i + 1}", FS["body"], 700, WHITE, anchor="middle")
        tl = wrap(it["title"], FS["body"], cw_ - 24, True)
        p_, y = para(cx, cy + 96, tl, FS["body"], 700, TEXT, "middle", 1.25)
        o += p_
        if it.get("text"):
            bl = wrap(it["text"], FS["min"], cw_ - 32)
            p_, y = para(cx, y + 42, bl, FS["min"], 400, MUTED, "middle", 1.3)
            o += p_
        if y + 10 > BODY_BOT:
            raise FitError(f"step {i + 1} text overflows ({it['title']!r})")
    return o


def L_emphasis(s):
    il = s.get("illust")
    lines = wrap(s["statement"], 52, 720, True)
    if len(lines) > 3:
        raise FitError(f"emphasis statement > 3 lines: {s['statement']!r}")
    sub = wrap(s["sub"], FS["body"], 720) if s.get("sub") else []
    ih = 140 if il else 0
    h = ih + (24 if il else 0) + block_h(len(lines), 52, 1.3) + (28 + block_h(len(sub), FS["body"]) if sub else 0)
    top = vcenter(h)
    o = ""
    if il:
        o += ill(il, CX - 70, top, 140)
    y = top + ih + (24 if il else 0) + 52 * 0.78
    p_, y = para(CX, y, lines, 52, 700, TEXT, "middle", 1.3)
    o += p_
    if sub:
        o += para(CX, y + 52 * 0.22 + 28 + FS["body"] * 0.78, sub, FS["body"], 400, MUTED, "middle")[0]
    return o


def L_quote(s):
    il = s.get("illust")
    right = 576 if il else X1
    pad = 36
    fs = FS["h2"]
    lines = wrap(s["text"], fs, right - X0 - 2 * pad - 8)
    if len(lines) > 4:
        fs = FS["body"]
        lines = wrap(s["text"], fs, right - X0 - 2 * pad - 8)
    if 48 + 24 + block_h(len(lines), fs) + 2 * pad > BODY_BOT - BODY_TOP:
        fs = FS["min"]
        lines = wrap(s["text"], fs, right - X0 - 2 * pad - 8)
    src = s.get("source", "")
    h = 48 + 24 + block_h(len(lines), fs) + 2 * pad
    top = vcenter(h)
    o = r(X0, top, right - X0, h, CARD, 24) + r(X0, top, 10, h, NAVY)
    o += pill(X0 + pad, top + pad, src, 28, WHITE, NAVY, LINE)[0] if src else ""
    o += para(X0 + pad + 8, top + pad + 48 + 24 + fs * 0.78 + 4, lines, fs, 400, TEXT)[0]
    if il:
        o += ill(il, 600, vcenter(248), 248)
    return o


def L_stat(s):
    il = s.get("illust")
    val, unit = str(s["value"]), s.get("unit", "")
    vw = text_w(val, 140, True)
    o = ""
    desc = wrap(s.get("desc", ""), FS["body"], 520 if il else CW) if s.get("desc") else []
    lab = s.get("caption")
    if lab and text_w(lab, FS["min"], True) > (520 if il else CW):
        raise FitError(f"stat caption too long for one line: {lab!r}")
    h = (FS["min"] + 24 if lab else 0) + 112 + 64 + block_h(len(desc), FS["body"])
    top = vcenter(h)
    y = top
    if lab:
        o += t(X0, y + FS["min"] * 0.78, lab, FS["min"], 700, MUTED)
        y += FS["min"] + 24
    o += t(X0 - 6, y + 108, val, 140, 700, NAVY)
    if unit:
        o += t(X0 + vw + 8, y + 108, unit, 56, 700, NAVY)
    if X0 + vw + 8 + text_w(unit, 56, True) > (584 if il else X1):
        raise FitError(f"stat value {val}{unit} runs into the illustration — drop illust or shorten the value")
    o += para(X0, y + 112 + 64 + FS["body"] * 0.78, desc, FS["body"], 400, TEXT)[0]
    if il:
        o += ill(il, 600, vcenter(248), 248)
    return o


def L_case(s):
    il = s.get("illust", "talk")
    right = 568
    pad = 32
    lines = []
    for x in s.get("lines", []):
        lines += wrap(x, FS["key"], right - X0 - 2 * pad)
    title = wrap(s.get("heading", ""), FS["h2"], right - X0 - 2 * pad, True) if s.get("heading") else []
    h = pad + 44 + 20 + (block_h(len(title), FS["h2"], 1.3) + 20 if title else 0) + block_h(len(lines), FS["key"]) + pad
    top = vcenter(h)
    o = r(X0, top, right - X0, h, CARD, 24)
    o += pill(X0 + pad, top + pad, s.get("tag", "사례"), 28, NAVY, WHITE)[0]
    y = top + pad + 44 + 20
    if title:
        p_, yl = para(X0 + pad, y + FS["h2"] * 0.78, title, FS["h2"], 700, TEXT, lh=1.3)
        o += p_
        y = yl + FS["h2"] * 0.22 + 20
    o += para(X0 + pad, y + FS["key"] * 0.78, lines, FS["key"], 400, TEXT)[0]
    o += ill(il, 600, vcenter(248), 248)
    return o


def L_screen(s):
    """Device frame (+ optional screenshot) and 2–4 short steps — replaces gray monitor mockups."""
    dx, dy, dw, dh = X0, BODY_TOP + 20, 440, 276
    o = r(dx, dy, dw, dh, WHITE, 18, NAVY, 3)
    sx, sy, sw_, sh = dx + 16, dy + 16, dw - 32, dh - 32
    if s.get("image"):
        o += (f'  <image href="../images/{s["image"]}" x="{sx}" y="{sy}" width="{sw_}" height="{sh}" '
              f'preserveAspectRatio="xMidYMid slice"/>\n')
    else:
        o += r(sx, sy, sw_, sh, SOFT, 6) + r(sx, sy, sw_, 36, NAVY, 6) + r(sx, sy + 20, sw_, 16, NAVY)
        for k, x in enumerate((sx + 20, sx + 44, sx + 68)):
            o += circ(x, sy + 18, 6, WHITE)
        o += r(sx + 20, sy + 56, 104, sh - 76, WHITE, 8)
        for k in range(4):
            o += ln(sx + 36, sy + 80 + k * 32, sx + 104, sy + 80 + k * 32, NAVY if k == 0 else LINE2, 6)
        o += r(sx + 140, sy + 56, sw_ - 160, 64, WHITE, 8) + ln(sx + 160, sy + 88, sx + 300, sy + 88, NAVY, 6)
        o += r(sx + 140, sy + 136, (sw_ - 176) / 2, sh - 156, WHITE, 8) + r(sx + 156 + (sw_ - 176) / 2, sy + 136, (sw_ - 176) / 2, sh - 156, WHITE, 8)
    o += path(f"M{dx - 20} {dy + dh + 4} L{dx + dw + 20} {dy + dh + 4} L{dx + dw + 4} {dy + dh + 28} L{dx - 4} {dy + dh + 28} Z", WHITE, NAVY, 3)
    o += ln(dx + dw / 2 - 40, dy + dh + 14, dx + dw / 2 + 40, dy + dh + 14, NAVY, 3)
    items = s.get("steps", [])
    if not 1 <= len(items) <= 4:
        raise FitError("screen takes 1–4 steps")
    TX, maxw = dx + dw + 40 + 56, X1 - (dx + dw + 40 + 56)
    rows = [(wrap(x, FS["min"], maxw)) for x in items]
    total = sum(block_h(len(rw), FS["min"], 1.35) for rw in rows) + 28 * (len(rows) - 1)
    y = vcenter(max(total, 0))
    for i, rw in enumerate(rows):
        o += circ(dx + dw + 40 + 20, y + 16, 20, NAVY) + t(dx + dw + 60, y + 25, f"{i + 1}", 28, 700, WHITE, anchor="middle")
        p_, yl = para(TX, y + FS["min"] * 0.78 + 2, rw, FS["min"], 700 if i == 0 and len(items) == 1 else 400, TEXT, lh=1.35)
        o += p_
        y += block_h(len(rw), FS["min"], 1.35) + 28
    return o


def _img(href, x, y, w, h, fit="slice"):
    par = "xMidYMid meet" if fit == "meet" else "xMidYMid slice"
    o = r(x, y, w, h, CARD) if fit == "meet" else ""
    o += (f'  <image href="../images/{href}" x="{round(x, 1)}" y="{round(y, 1)}" width="{round(w, 1)}" '
          f'height="{round(h, 1)}" preserveAspectRatio="{par}"/>\n')
    return o + r(x, y, w, h, "none", None, LINE, 2)


def L_photo(s):
    """1–4 content photos (teaching material, not decoration) + optional caption and 1–3 side points."""
    imgs = s.get("images") or []
    if not 1 <= len(imgs) <= 4:
        raise FitError("photo takes 1–4 images")
    fit = s.get("fit", "slice")
    pts = s.get("points") or []
    if len(pts) > 4:
        raise FitError("photo takes at most 4 points")
    cap = wrap(s["caption"], FS["min"], CW if not pts else 440, True) if s.get("caption") else []
    if len(cap) > 1:
        raise FitError(f"photo caption must fit one line: {s['caption']!r}")
    ax, aw = X0, (440 if pts else CW)
    ay, ah = BODY_TOP, BODY_BOT - BODY_TOP - (48 if cap else 0)
    g = 12
    n = len(imgs)
    if n == 1:
        cells = [(ax, ay, aw, ah)]
    elif n == 2:
        cw2 = (aw - g) / 2
        cells = [(ax, ay, cw2, ah), (ax + cw2 + g, ay, cw2, ah)]
    elif n == 3:
        big = (aw - g) * 0.58
        sm = aw - g - big
        hh = (ah - g) / 2
        cells = [(ax, ay, big, ah), (ax + big + g, ay, sm, hh), (ax + big + g, ay + hh + g, sm, hh)]
    else:
        cw2, hh = (aw - g) / 2, (ah - g) / 2
        cells = [(ax, ay, cw2, hh), (ax + cw2 + g, ay, cw2, hh), (ax, ay + hh + g, cw2, hh), (ax + cw2 + g, ay + hh + g, cw2, hh)]
    o = "".join(_img(im, *c, fit=fit) for im, c in zip(imgs, cells))
    if cap:
        o += t(ax, BODY_BOT - 8, cap[0], FS["min"], 700, TEXT)
    if pts:
        TX, maxw = ax + aw + 32 + 44, X1 - (ax + aw + 32 + 44)
        rows = [wrap(p_, FS["min"], maxw) for p_ in pts]
        total = sum(block_h(len(rw), FS["min"], 1.35) for rw in rows) + 28 * (len(rows) - 1)
        y = vcenter(total)
        for i, rw in enumerate(rows):
            o += circ(ax + aw + 32 + 18, y + 14, 18, NAVY) + t(ax + aw + 50, y + 23, f"{i + 1}", 28, 700, WHITE, anchor="middle")
            o += para(TX, y + FS["min"] * 0.78 + 2, rw, FS["min"], 400, TEXT, lh=1.35)[0]
            y += block_h(len(rw), FS["min"], 1.35) + 28
    return o


def L_quiz(s):
    qfs = FS["h2"]
    q = wrap(s["question"], qfs, CW, True)
    if len(q) > 2:                      # long source question: 32px, up to 3 lines
        qfs = FS["body"]
        q = wrap(s["question"], qfs, CW, True)
    if len(q) > 3:
        raise FitError(f"quiz question > 3 lines: {s['question']!r}")
    o = ""
    p_, y = para(X0, BODY_TOP + 12 + qfs * 0.78, q, qfs, 700, TEXT, lh=1.3)
    o += p_
    top = y + qfs * 0.22 + (32 if len(q) < 3 else 20)
    if s.get("type") == "blank":            # fill-in-the-blank: big answer box
        bw, bh = 360, min(150, BODY_BOT - top)
        o += r(CX - bw / 2, top, bw, bh, CARD, 28, LINE, 2)
        o += r(CX - bw / 2 + 40, top + bh / 2 + 22, bw - 80, 6, NAVY, 3)
        o += t(CX, top + bh / 2 + 4, "?", 72, 700, NAVY, anchor="middle")
    elif s.get("type", "ox") == "ox":
        sz = min(200, BODY_BOT - top)
        for k, (cx, lab) in enumerate(((CX - 24 - sz / 2, s.get("o_label", "그렇다")), (CX + 24 + sz / 2, s.get("x_label", "아니다")))):
            o += r(cx - sz / 2, top, sz, sz - 44, CARD, 28, LINE, 2)
            mid = top + (sz - 44) / 2
            o += o_mark(cx, mid, 44, NAVY, 13) if k == 0 else x_mark(cx, mid, 38, MUTED, 13)
            o += t(cx, top + sz + 4, lab, FS["min"], 700, TEXT, anchor="middle")
    else:
        opts = s["options"]
        if not 2 <= len(opts) <= 4:
            raise FitError("choice quiz takes 2–4 options")
        avail = BODY_BOT - top
        for g, ofs in ((12, FS["body"]), (8, FS["min"])):
            wrapped = [wrap(x, ofs, CW - 96) for x in opts]
            hs = [max(52, block_h(len(w_), ofs, 1.2) + 18) for w_ in wrapped]
            if max(len(w_) for w_ in wrapped) <= 2 and sum(hs) + g * (len(opts) - 1) <= avail:
                break
        else:
            raise FitError("too many/long options for the body area — shorten the question or options")
        y = top
        for i, (w_, rh) in enumerate(zip(wrapped, hs)):
            cr_ = 22
            o += r(X0, y, CW, rh, CARD, min(rh / 2, 28), LINE, 2)
            o += circ(X0 + 34, y + rh / 2, cr_, NAVY) + t(X0 + 34, y + rh / 2 + 10, f"{i + 1}", 28, 700, WHITE, anchor="middle")
            bh = block_h(len(w_), ofs, 1.2)
            o += para(X0 + 72, y + (rh - bh) / 2 + ofs * 0.8, w_, ofs, 400, TEXT, lh=1.2)[0]
            y += rh + g
    return o


def L_answer(s):
    q = wrap(s.get("question", ""), FS["min"], CW) if s.get("question") else []
    o = ""
    y = BODY_TOP + 4
    if q:
        if len(q) > 3:
            raise FitError("answer: question longer than 3 lines at 28px")
        p_, yl = para(X0, y + FS["min"] * 0.78, q, FS["min"], 400, MUTED, lh=1.35)
        o += p_
        y = yl + FS["min"] * 0.22 + 24
    ans = str(s["answer"])
    R = 44
    o += circ(X0 + R, y + R, R, NAVY)
    if ans.upper() == "O":
        o += o_mark(X0 + R, y + R, 20, WHITE, 8)
    elif ans.upper() == "X":
        o += x_mark(X0 + R, y + R, 17, WHITE, 8)
    else:
        o += t(X0 + R, y + R + 13, ans, 36, 700, WHITE, anchor="middle")
    head = s.get("headline", "정답")
    if text_w(head, FS["h1"], True) > CW - 140:
        raise FitError(f"answer headline too long: {head!r}")
    o += t(X0 + 2 * R + 28, y + R + 15, head, FS["h1"], 700, NAVY)
    y += 2 * R + 20
    ex = []
    for x in s.get("explain", []):
        ex += wrap(x, FS["body"], CW - 64)
    if not ex:
        return o
    h = block_h(len(ex), FS["body"]) + 56
    if y + h > BODY_BOT + 0.5:
        raise FitError("answer explanation overflows — max ≈3 lines")
    o += r(X0, y, CW, h, CARD, 24)
    o += para(X0 + 32, y + 28 + FS["body"] * 0.78, ex, FS["body"], 400, TEXT)[0]
    return o


LAYOUTS = {
    # name: (fn, shell?, role, family, page_family, block_type)
    "cover": (L_cover, True, "cover", "structure", "title", "image"),
    "chapter": (L_chapter, True, "context", "structure", "chapter", "image"),
    "ending": (L_ending, True, "cta", "structure", "end", "image"),
    "agenda": (L_agenda, False, "agenda", "structure", "body", "icon_group"),
    "concept": (L_concept, False, "concept", "insight", "body", "image"),
    "bullets": (L_bullets, False, "concept", "breakdown", "body", "icon_group"),
    "cards": (L_cards, False, "concept", "breakdown", "body", "icon_group"),
    "compare": (L_compare, False, "concept", "compare", "body", "infographic"),
    "steps": (L_steps, False, "concept", "process", "body", "diagram_flow"),
    "emphasis": (L_emphasis, False, "insight", "insight", "body", "callout"),
    "quote": (L_quote, False, "evidence", "data", "body", "callout"),
    "stat": (L_stat, False, "evidence", "data", "body", "metric_cards"),
    "case": (L_case, False, "example", "visual", "body", "image"),
    "screen": (L_screen, False, "example", "visual", "body", "image"),
    "photo": (L_photo, False, "example", "visual", "body", "image"),
    "quiz": (L_quiz, False, "exercise", "compare", "body", "infographic"),
    "answer": (L_answer, False, "exercise", "insight", "body", "callout"),
    "summary": (L_summary, False, "recap", "structure", "body", "icon_group"),
}

FNAME_TAG = {"cover": "cover", "chapter": "chapter", "ending": "ending"}


def build_page(i, s):
    lay = s.get("layout")
    if lay not in LAYOUTS:
        raise FitError(f"unknown layout {lay!r} — one of: {', '.join(LAYOUTS)}")
    fn, shell = LAYOUTS[lay][:2]
    global CUR
    CUR = s
    if s.get("image") and not s.get("illust") and lay not in ("screen", "photo"):
        s["illust"] = "idea"      # placeholder name; ill() draws the image instead
    slug = re.sub(r"[^0-9A-Za-z가-힣]+", "_", str(s.get("title") if not isinstance(s.get("title"), list) else " ".join(s["title"])) or lay).strip("_")[:24]
    fname = f"{i:0{WIDTH}d}_{FNAME_TAG.get(lay, lay)}_{slug}.svg"
    global BODY_BOT
    nk = len(key_lines(s.get("key")))
    BODY_BOT = 552 if shell else (628 if nk == 0 else (528 if nk == 2 else 552))   # no key → body takes its band
    try:
        body = fn(s)
    finally:
        BODY_BOT = 552
    if shell:
        navy_page(fname, body)
    else:
        content_page(fname, s, body)
    return fname
