"""vkit.layouts — the layout library. Every layout draws only inside the content card
(x 64–844); the presenter zone (x ≥ 896) and the subtitle zone (y ≥ 644) stay empty.

Each layout is `fn(p) -> body_svg` where p is one page dict from the deck spec. Field reference:
references/layouts.md. Shared fields handled by build_deck.py: layout, section, title, gm, notes.
"""
import illust
import prim
from prim import (block, check_mark, circle, fit, icon, lines, line, measure, path, plain, poly, rect, split_two_tone,
                  text, two_tone, warn, wrap, esc, r1)
from tokens import (BODY, BODY_BOTTOM, BODY_TOP, CONTENT_L, CONTENT_R, CONTENT_W, CX, GREEN, INK, LAV, LINE,
                    MINT, MINT_BG, MINT_PALE, MUTED, NAVY, SERIES, T_BIG, T_BODY, T_H2, T_SMALL, TEAL, WHITE)
from frame import title as title_line

L, R = CONTENT_L, CONTENT_R
TOP, BOT = BODY_TOP, BODY_BOTTOM


# ── helpers ──────────────────────────────────────────────────────────────────

def items(p, key="items", lo=1, hi=6):
    raw = p.get(key) or []
    out = []
    for it in raw:
        if isinstance(it, str):
            out.append({"title": it})
        elif isinstance(it, (list, tuple)):
            out.append({"title": it[0], "desc": it[1] if len(it) > 1 else ""})
        else:
            out.append(dict(it))
    if not lo <= len(out) <= hi:
        warn(f"layout '{p.get('layout')}' expects {lo}–{hi} {key}, got {len(out)} — extra items dropped")
        out = out[:hi]
    return out


def ramp(n):
    """Colour order for n solid cards (light → dark, like the template)."""
    return {1: [GREEN], 2: [GREEN, TEAL], 3: [MINT, GREEN, TEAL], 4: [MINT, GREEN, TEAL, NAVY],
            5: [MINT, GREEN, TEAL, NAVY, NAVY]}[n]


def on(c):
    """Text colour on a filled shape: navy on the light mint fills, white on the dark fills."""
    return NAVY if c in (MINT, MINT_BG, MINT_PALE, LAV) else WHITE


def nice_max(v):
    """Round an axis maximum up to 1·2·2.5·5·10 × 10^k."""
    import math
    if v <= 0:
        return 1
    e = 10 ** math.floor(math.log10(v))
    for m in (1, 2, 2.5, 5, 10):
        if v <= m * e:
            return m * e
    return 10 * e


def ink_for(c):
    """Readable text colour for a coloured title on white."""
    return {MINT: GREEN, MINT_BG: GREEN}.get(c, c)


def vcenter(h, top=TOP, bot=BOT):
    return top + max(0, (bot - top - h) / 2)


def ill(p, x, y, w, h, default=None, backdrop=True):
    name = p.get("illust", default)
    if not name or name == "none":
        return ""
    if name == "auto":
        name = illust.pick(" ".join(str(v) for v in p.values() if isinstance(v, str)))
    return illust.place(name, x, y, w, h, backdrop)


def dotted(x1, y1, x2, y2, c=MINT):
    return line(x1, y1, x2, y2, c, 2, dash="2 5", cap="round")


# ── cover / agenda / section / ending (no GM) ───────────────────────────────

def cover(p):
    has_ill = p.get("illust", "presenter") != "none"
    maxw = 440 if has_ill else CONTENT_W - 40
    x = L + 10 if has_ill else CX
    anchor = None if has_ill else "middle"
    a, b = split_two_tone(p.get("title", ""))
    rows = []                                        # (kind, text, size, colour, height)
    if p.get("eyebrow"):
        rows.append(("eyebrow", prim.deco(p["eyebrow"]), 18, GREEN, 50))
    for part, c in ((a, GREEN), (b, NAVY)):
        if part:
            ls_, fs = fit(part, 52, maxw, 2, 900, 40)
            rows += [("title", s_, fs, c, fs * 1.22) for s_ in ls_]
    if p.get("subtitle"):
        (sub,), fs = fit(p["subtitle"], 19, maxw - 48, 1, 700, 16)
        rows.append(("pill", sub, fs, NAVY, 76))
    if p.get("meta"):
        rows.append(("meta", p["meta"], 17, BODY, 36))
    total = sum(r_[4] for r_ in rows)
    y = 120 + max(0, (520 - 120 - total) / 2)
    o = ""
    for kind, s_, fs, c, hh in rows:
        if kind == "eyebrow":
            o += text(x, y + 20, s_, fs, 600, c, anchor)
        elif kind == "title":
            o += text(x, y + fs * 0.95, s_, fs, 900, c, anchor, ls=round(-0.03 * fs, 2))
        elif kind == "pill":
            w = measure(s_, fs, 700) + 56
            px = x if has_ill else CX - w / 2
            o += rect(px, y + 16, w, 48, c, rx=24) + text(px + w / 2, y + 46, s_, fs, 700, WHITE, "middle")
        else:
            o += text(x, y + 28, s_, fs, 500, c, anchor)
        y += hh
    if has_ill:
        o += ill(p, 520, 150, 330, 330, "presenter")
    return o


def agenda(p):
    its = items(p, lo=2, hi=6)
    n = len(its)
    has_ill = p.get("illust", "book") != "none"
    x, w = (L + 16, 476) if has_ill else (CX - 300, 600)
    gap, h = (14, 50) if n <= 5 else (10, 44)
    y = vcenter(n * h + (n - 1) * gap, TOP + 6)
    o = ""
    for i, it in enumerate(its):
        c = GREEN if i % 2 == 0 else MINT
        o += rect(x, y, w, h, c, rx=h / 2)
        no = str(it.get("no", "" if prim.LOCK else i + 1))
        o += circle(x + h / 2, y + h / 2, h / 2 - 7, WHITE)
        if no:
            o += text(x + h / 2, y + h / 2 + 6, no, 17 if len(no) < 2 else 15, 700, ink_for(c) if c != MINT else NAVY, "middle")
        (s,), fs = fit(it["title"], 19, w - h - 40, 1, 700, 15)
        o += text(x + h + 18, y + h / 2 + fs * 0.36, s, fs, 700, on(c))
        y += h + gap
    if has_ill:
        o += ill(p, 588, 210, 250, 300, "book")
    return o


def section(p):
    """Unit opener: label + big number + title (+ desc, or a bullet list of what the unit covers)."""
    o = ""
    has_ill = p.get("illust", "auto") != "none"
    x = L + 10
    maxw = 450 if has_ill else 700
    no = p.get("no", p.get("number", "" if prim.LOCK else 1))
    label = p.get("label", "" if prim.LOCK else "PART")
    its = items(p, lo=0, hi=5) if p.get("items") else []
    top = 222 if not its else 200
    if label:
        o += text(x, top, label, 18, 700, GREEN, ls=4)
    y = top + 4
    if no != "":
        o += text(x - 4, top + 96, f"{int(no):02d}" if isinstance(no, int) else str(no), 96 if its else 104, 900,
                  GREEN, ls=-3)
        y = top + 160
    t_svg, n, fs, hh = block(x, y, plain(p.get("title", "")), 34 if its else 40, maxw, 2, 44, 800, NAVY, min_fs=24)
    o += t_svg
    y += hh + 16
    if p.get("desc"):
        o += block(x, y, p["desc"], T_BODY + 1, maxw, 3, 28, 400, BODY)[0]
    for it in its:
        ls_, f2 = fit(it["title"], 18, maxw - 24, 2, 500, 15)
        o += circle(x + 5, y - 6, 4, GREEN) + lines(x + 20, y, ls_, f2, 25, 500, INK)
        y += 25 * len(ls_) + 12
    if has_ill:
        o += ill(p, 520, 170, 320, 330, "auto")
    return o


def ending(p):
    """Closing page; with `no` it closes a unit (number + unit title + closing line)."""
    o = ""
    has_ill = p.get("illust", "trophy") != "none"
    x, anchor, maxw = (L + 10, None, 440) if has_ill else (CX, "middle", 700)
    y = 214
    if p.get("no"):
        o += text(x - (4 if not anchor else 0), 250, str(p["no"]), 80, 900, GREEN, anchor, ls=-2)
        y = 296
    if p.get("subtitle"):
        sub = p["subtitle"] if p.get("no") else prim.deco(p["subtitle"])
        sl, sfs = fit(sub, 21 if p.get("no") else 19, maxw, 2, 700, 15)
        o += lines(x, y, sl, sfs, 30, 700 if p.get("no") else 600, NAVY if p.get("no") else GREEN, anchor)
        y += 30 * len(sl)
    big = plain(p.get("title", "" if prim.LOCK else "감사합니다"))
    if big:
        (s_,), fs = fit(big, 60 if p.get("no") else 64, maxw, 1, 900, 40)
        o += text(x, y + 76, s_, fs, 900, NAVY, anchor, ls=round(-0.03 * fs, 2))
        y += 76
    y += 52
    if p.get("desc"):
        svg, n, _, hh = block(x, y, p["desc"], 18, maxw, 3, 28, 400, BODY, anchor)
        o += svg
        y += hh + 14
    for i, s_ in enumerate(p.get("lines") or []):
        o += text(x, y + 10 + i * 28, s_, 17, 600 if i == 0 else 400, NAVY if i == 0 else BODY, anchor)
    if has_ill:
        o += ill(p, 540, 160, 300, 320, "trophy")
    return o


# ── text-led layouts ─────────────────────────────────────────────────────────

def statement(p):
    """Lead lines + one highlighted claim (+ optional body) — the reference video's layout."""
    has_ill = p.get("illust", "auto") != "none"
    x, anchor, maxw = (L + 24, None, 450) if has_ill else (CX, "middle", 720)
    lead = p.get("lines") or ([p["lead"]] if p.get("lead") else [])
    blocks = []
    for s in lead:
        for ln_ in wrap(s, 28, maxw, 500):
            blocks.append(("lead", ln_))
    hl_lines, hfs = fit(p.get("highlight", ""), 36, maxw, 2, 800, 28) if p.get("highlight") else ([], 36)
    body_lines, bfs = fit(p.get("body", ""), T_BODY, maxw, 4, 400, 15) if p.get("body") else ([], T_BODY)
    h = len(blocks) * 42 + len(hl_lines) * (hfs * 1.3) + (14 if hl_lines else 0) + (len(body_lines) * 27 + 24 if body_lines else 0)
    y = vcenter(h) + 30
    o = ""
    for _, s in blocks:
        o += text(x, y, s, 28, 500, INK, anchor)
        y += 42
    if hl_lines:
        y += 14
        for s in hl_lines:
            o += text(x, y, s, hfs, 800, GREEN, anchor, ls=-0.8)
            w = measure(s, hfs, 800)
            ux = x if not anchor else x - w / 2
            o += rect(ux, y + 8, w, 4, GREEN, rx=2)
            y += hfs * 1.3
    if body_lines:
        y += 24
        o += lines(x, y, body_lines, bfs, 27, 400, BODY, anchor)
    if has_ill:
        o += ill(p, 544, 190, 300, 350, "auto")
    return o


def points(p):
    """Numbered key points (2–5) with an optional illustration on the right."""
    its = items(p, lo=1, hi=5)
    has_ill = p.get("illust", "auto") != "none"
    x, w = (L + 16, 470) if has_ill else (L + 40, 700)
    rows = []
    for it in its:
        tl, tfs = fit(it["title"], 21, w - 56, 1, 700, 17)
        dl, dfs = fit(it.get("desc", ""), 16, w - 56, 2, 400, 15) if it.get("desc") else ([], 16)
        rows.append((tl, tfs, dl, dfs, 34 + len(dl) * 24))
    gap = 22 if len(its) <= 3 else 14
    total = sum(r_[4] for r_ in rows) + gap * (len(rows) - 1)
    y = vcenter(total)
    o = ""
    for i, (tl, tfs, dl, dfs, hh) in enumerate(rows):
        c = SERIES[i % len(SERIES)] if p.get("color", "series") == "series" else GREEN
        o += circle(x + 17, y + 16, 17, c) + text(x + 17, y + 22, str(i + 1), 16, 700, WHITE, "middle")
        o += text(x + 50, y + 23, tl[0], tfs, 700, NAVY)
        o += lines(x + 50, y + 50, dl, dfs, 24, 400, BODY)
        y += hh + gap
    if has_ill:
        o += ill(p, 568, 200, 272, 320, "auto")
    return o


def icon_list(p):
    """Big statement on the left + 2–4 icon rows on the right (template p.3)."""
    its = items(p, lo=2, hi=4)
    has_title = bool(p.get("title"))
    top = TOP if has_title else 126
    o = ""
    if p.get("headline"):
        a, b = split_two_tone(p["headline"])
        segs = [(s, GREEN) for s in (wrap(a, 38, 300, 800) if a else [])] + [(s, NAVY) for s in wrap(b, 38, 300, 800)]
        fs = 38 if len(segs) <= 3 else 32
        y = vcenter(len(segs) * fs * 1.25, top) + fs
        for s, c in segs:
            o += text(L + 12, y, s, fs, 800, c, ls=-1)
            y += fs * 1.25
    x0 = 384 if p.get("headline") else L + 60
    tw = R - x0 - 96
    n = len(its)
    step = (BOT - top) / n
    for i, it in enumerate(its):
        c = [GREEN, TEAL, NAVY, MINT][i]
        cy = top + step * (i + 0.5)
        o += circle(x0 + 38, cy, 38, c) + icon(it.get("icon", "point"), x0 + 20, cy - 18, 36, WHITE)
        o += text(x0 + 96, cy - 10, fit(it["title"], 21, tw, 1, 700, 17)[0][0], 21, 700, ink_for(c))
        if it.get("desc"):
            dl, dfs = fit(it["desc"], 16, tw, 2, 400, 14)
            o += lines(x0 + 96, cy + 18, dl, dfs, 23, 400, BODY)
    return o


# ── card layouts ─────────────────────────────────────────────────────────────

def cards(p):
    """2–4 solid colour cards: number or icon, title, description (template p.4 / p.16)."""
    its = items(p, lo=2, hi=4)
    n = len(its)
    gap = 18
    w = (CONTENT_W - 24 - gap * (n - 1)) / n
    cols = ramp(n)
    tws = w - 40
    prepared = []
    for it in its:
        tl, tfs = fit(it["title"], T_H2, tws, 2, 700, 17)
        dl, dfs = fit(it.get("desc", ""), 16, tws, 5, 400, 14) if it.get("desc") else ([], 16)
        prepared.append((tl, tfs, dl, dfs))
    max_t = max(len(x[0]) for x in prepared)
    max_d = max(len(x[2]) for x in prepared)
    h = 64 + max_t * 30 + (18 + max_d * 24 if max_d else 0) + 30
    h = max(h, 240)
    y = vcenter(h)
    o = ""
    for i, (it, (tl, tfs, dl, dfs)) in enumerate(zip(its, prepared)):
        x = L + 12 + i * (w + gap)
        cxi = x + w / 2
        o += rect(x, y, w, h, cols[i], rx=18)
        if it.get("icon"):
            o += icon(it["icon"], cxi - 16, y + 22, 32, on(cols[i]))
        else:
            o += text(cxi, y + 44, str(i + 1), 18, 600, on(cols[i]), "middle")
        ty = y + 64 + 26
        o += lines(cxi, ty, tl, tfs, 30, 700, on(cols[i]), "middle")
        o += lines(cxi, ty + len(tl) * 30 + 18, dl, dfs, 24, 400, on(cols[i]), "middle")
    return o


def stats(p):
    """2–4 big-number cards (template p.6)."""
    its = items(p, lo=2, hi=4)
    n = len(its)
    gap = 18
    w = (CONTENT_W - 24 - gap * (n - 1)) / n
    cols = ramp(n)
    h = 250
    y = vcenter(h)
    o = ""
    for i, it in enumerate(its):
        x = L + 12 + i * (w + gap)
        cxi = x + w / 2
        o += rect(x, y, w, h, cols[i], rx=18)
        tc = on(cols[i])
        o += text(cxi, y + 50, fit(it.get("label", ""), 17, w - 32, 1, 600, 14)[0][0], 17, 600, tc, "middle")
        (v,), vfs = fit(str(it.get("value", it.get("title", ""))), T_BIG, w - 24, 1, 800, 30)
        o += text(cxi, y + 132, v, vfs, 800, tc, "middle", ls=-1)
        if it.get("desc"):
            dl, dfs = fit(it["desc"], 15, w - 36, 2, 400, 14)
            o += lines(cxi, y + 190, dl, dfs, 22, 400, tc, "middle")
    return o


def illust_cards(p):
    """2–4 illustration cards: title (+ text); 4 items → 2 × 2 tiles. Template p.13 photos are replaced
    by library illustrations. `numbered` (default on; off in content-lock mode) adds number badges."""
    its = items(p, lo=2, hi=4)
    n = len(its)
    numbered = p.get("numbered", not prim.LOCK)
    o = ""

    def pick_(it):
        return it.get("illust") or illust.pick(it["title"] + it.get("desc", ""))

    if n == 4:
        gap = 18
        w, h = (CONTENT_W - 24 - gap) / 2, (BOT - TOP - 10 - gap) / 2
        for i, it in enumerate(its):
            x, y = L + 12 + (i % 2) * (w + gap), TOP + 4 + (i // 2) * (h + gap)
            c = [GREEN, TEAL, NAVY, GREEN][i]
            o += rect(x, y, w, h, MINT_BG, rx=16)
            o += illust.place(pick_(it), x + 10, y + 10, w * 0.46, h - 20, backdrop=False)
            tx, tw = x + w * 0.5, w * 0.46
            tl, tfs = fit(it["title"], 21, tw, 2, 800, 16)
            dl, dfs = fit(it.get("desc", ""), 15, tw, 3, 400, 13) if it.get("desc") else ([], 15)
            hh = len(tl) * 28 + (len(dl) * 22 + 8 if dl else 0)
            ty = y + (h - hh) / 2 + 20
            o += lines(tx, ty, tl, tfs, 28, 800, c)
            o += lines(tx, ty + len(tl) * 28 + 6, dl, dfs, 22, 400, BODY)
            if numbered:
                o += circle(x + 24, y + 24, 15, c) + text(x + 24, y + 30, str(i + 1), 15, 700, WHITE, "middle")
        return o
    gap = 20
    w = (CONTENT_W - 24 - gap * (n - 1)) / n
    y = TOP + 12
    ih = 168 if n == 3 else 190
    for i, it in enumerate(its):
        x = L + 12 + i * (w + gap)
        c = [GREEN, TEAL, NAVY][i]
        o += rect(x, y, w, ih, MINT_BG, rx=16)
        o += illust.place(pick_(it), x + 12, y + 8, w - 24, ih - 16, backdrop=False)
        if numbered:
            o += circle(x + 26, y + 26, 16, c) + text(x + 26, y + 32, str(i + 1), 16, 700, WHITE, "middle")
        tl, tfs = fit(it["title"], 20, w - 16, 1, 700, 16)
        o += text(x + w / 2, y + ih + 40, tl[0], tfs, 700, c, "middle")
        if it.get("desc"):
            dl, dfs = fit(it["desc"], 15, w - 20, 3, 400, 14)
            o += lines(x + w / 2, y + ih + 70, dl, dfs, 23, 400, BODY, "middle")
    return o


# ── structure layouts ────────────────────────────────────────────────────────

def flow(p):
    """3–5 joined circles with icon + short text (template p.7)."""
    its = items(p, lo=3, hi=5)
    n = len(its)
    span = CONTENT_W - 30
    step = span / n
    r_ = min(step * 0.56, 108)
    cy = vcenter(2 * r_) + r_
    x0 = L + 15 + step / 2
    o = rect(x0, cy - r_ * 0.62, step * (n - 1), r_ * 1.24, MINT)
    for i in range(n):
        o += circle(x0 + i * step, cy, r_, MINT)
    for i, it in enumerate(its):
        cxi = x0 + i * step
        o += text(cxi, cy - r_ * 0.55, str(i + 1), 17, 700, NAVY, "middle")
        o += icon(it.get("icon", "point"), cxi - 18, cy - r_ * 0.45, 36, NAVY)
        tl, tfs = fit(it["title"], 19, r_ * 1.55, 2, 700, 14)
        o += lines(cxi, cy + r_ * 0.3, tl, tfs, 25, 700, NAVY, "middle")
    if any(it.get("desc") for it in its):
        warn("flow: 'desc' is not drawn (circles hold a short title only) — move detail to notes")
    return o


def compare(p):
    """A vs B panels (template p.9). left/right: {title, items[]} — left is the 'before / not' side."""
    lf, rt = p.get("left", {}), p.get("right", {})
    pw = 350
    lx, rx_ = L + 12, R - 12 - pw
    y0, h = TOP + 30, BOT - TOP - 40
    o = rect(lx, y0, pw, h, LAV, rx=22) + rect(rx_, y0, pw, h, MINT_BG, rx=22)
    for x, side, c in ((lx, lf, NAVY), (rx_, rt, GREEN)):
        (tt,), tfs = fit(prim.deco(side.get("title", "")), 19, pw - 90, 1, 700, 15)
        tw = measure(tt, tfs, 700) + 60
        o += rect(x + (pw - tw) / 2, y0 - 26, tw, 50, c, rx=25) + text(x + pw / 2, y0 + 6, tt, tfs, 700, WHITE, "middle")
        its = side.get("items", [])[:5]
        step = (h - 50) / max(len(its), 1)
        for j, s in enumerate(its):
            dl, dfs = fit(s, 17, pw - 48, 2, 400, 14)
            o += lines(x + pw / 2, y0 + 50 + step * (j + 0.5), dl, dfs, 24, 500, INK if c == NAVY else INK, "middle",
                       valign_center=True)
    o += text(CX, y0 + h / 2 + 14, p.get("vs", "VS"), 36, 800, "#8A9BB8", "middle")
    return o


def before_after(p):
    """From → To panels with a dotted chevron (template p.10)."""
    lf, rt = p.get("left", {}), p.get("right", {})
    pw = 340
    lx, rx_ = L + 12, R - 12 - pw
    y0, h = TOP + 6, BOT - TOP - 14
    o = ""
    for x, side, c in ((lx, lf, NAVY), (rx_, rt, GREEN)):
        o += rect(x, y0, pw, h, c, rx=22)
        o += text(x + pw / 2, y0 + 48, fit(side.get("title", ""), 22, pw - 40, 1, 700, 17)[0][0], 22, 700, WHITE, "middle")
        its = side.get("items", [])[:5]
        step = (h - 90) / max(len(its), 1)
        for j, s in enumerate(its):
            cy = y0 + 80 + step * (j + 0.5)
            dl, dfs = fit(s, 17, pw - 50, 2, 400, 14)
            o += lines(x + pw / 2, cy, dl, dfs, 23, 400, WHITE, "middle", valign_center=True)
            if j < len(its) - 1:
                o += line(x + 30, y0 + 80 + step * (j + 1), x + pw - 30, y0 + 80 + step * (j + 1), WHITE, 1.5,
                          dash="2 4").replace("/>", ' stroke-opacity="0.45"/>')
    mx, my = CX, y0 + h / 2
    o += path(f"M{r1(mx - 14)},{r1(my - 46)} L{r1(mx + 18)},{r1(my)} L{r1(mx - 14)},{r1(my + 46)}", stroke=NAVY, sw=4,
              dash="1 7")
    return o


def pyramid(p):
    """3–5 tier pyramid with titles + descriptions (template p.11). Item 1 = top tier."""
    its = items(p, lo=3, hi=5)
    n = len(its)
    cols = [NAVY, TEAL, GREEN, MINT, MINT_BG][:n] if n == 5 else [NAVY, TEAL, GREEN, MINT][:n]
    top, bot = TOP + 4, BOT - 6
    gap = 10
    th = (bot - top - gap * (n - 1)) / n
    apex_x, base_w = L + 196, 380
    o = ""
    for i, (it, c) in enumerate(zip(its, cols)):
        y1 = top + i * (th + gap)
        y2 = y1 + th
        hw1 = base_w / 2 * (y1 - top) / (bot - top)
        hw2 = base_w / 2 * (y2 - top) / (bot - top)
        if i == 0:
            pts = [(apex_x, y1), (apex_x + hw2, y2), (apex_x - hw2, y2)]
        else:
            pts = [(apex_x - hw1, y1), (apex_x + hw1, y1), (apex_x + hw2, y2), (apex_x - hw2, y2)]
        o += poly(pts, c)
        nc = GREEN if c == MINT_BG else on(c)
        o += text(apex_x, y2 - th * 0.28, str(i + 1), 17, 700, nc, "middle")
        tx = apex_x + hw2 + 22
        tc = {MINT: GREEN, MINT_BG: GREEN}.get(c, c)
        o += line(apex_x + hw2 - 4, y2, R - 8, y2, tc, 1.5)
        (tt,), tfs = fit(it["title"], 19, R - tx - 10, 1, 700, 15)
        if it.get("desc"):
            o += text(tx, y2 - th * 0.55, tt, tfs, 700, tc)
            (dd,), dfs = fit(it["desc"], 15, R - tx - 10, 1, 400, 13)
            o += text(tx, y2 - th * 0.55 + 24, dd, dfs, 400, BODY)
        else:
            o += text(tx, y2 - th * 0.35, tt, tfs, 700, tc)
    return o


def hub(p):
    """Centre statement with 4 circles around it (template p.12)."""
    its = items(p, lo=4, hi=4)
    top = 128 if not p.get("title") else TOP
    o = ""
    cols = [NAVY, TEAL, GREEN, MINT]
    rr = 62
    ys = [top + (BOT - top) * 0.25, top + (BOT - top) * 0.75]
    xs = [L + 236, R - 236]
    pos = [(xs[0], ys[0]), (xs[1], ys[0]), (xs[0], ys[1]), (xs[1], ys[1])]
    cy_mid = (ys[0] + ys[1]) / 2
    import math
    ring = math.hypot(xs[0] - CX, ys[0] - cy_mid)
    o += circle(CX, cy_mid, ring, "none", stroke=MINT, sw=2).replace("/>", ' stroke-dasharray="2 6" stroke-linecap="round"/>')
    a, b = split_two_tone(p.get("headline", "핵심 | 포인트"))
    segs = [(s, GREEN) for s in (wrap(a, 34, 170, 800) if a else [])] + [(s, NAVY) for s in wrap(b, 34, 170, 800)]
    yy = cy_mid - (len(segs) - 1) * 21 + 12
    for s, c in segs:
        o += text(CX, yy, s, 34, 800, c, "middle", ls=-1)
        yy += 42
    for i, ((x, y), it, c) in enumerate(zip(pos, its, cols)):
        o += circle(x, y, rr, c)
        o += text(x, y - 22, str(i + 1), 15, 600, on(c), "middle")
        tl, tfs = fit(it["title"], 17, rr * 1.6, 2, 700, 13)
        o += lines(x, y + 8 if len(tl) == 1 else y - 2, tl, tfs, 22, 700, on(c), "middle")
        if it.get("desc"):
            dl, dfs = fit(it["desc"], 15, 150, 4, 400, 13)
            if x < CX:
                o += lines(x - rr - 16, y, dl, dfs, 22, 400, BODY, "end", valign_center=True)
            else:
                o += lines(x + rr + 16, y, dl, dfs, 22, 400, BODY, None, valign_center=True)
    return o


def qa(p):
    """Question → answer rows (template p.13)."""
    rows = (p.get("rows") or [])[:4]
    pw = 352
    lx, rx_ = L + 12, R - 12 - pw
    y = TOP + 8
    o = ""
    for x, lab, ttl, c in ((lx, "Q", p.get("q_title", "이런 점이 궁금합니다"), NAVY),
                           (rx_, "A", p.get("a_title", "이렇게 답합니다"), GREEN)):
        o += rect(x, y, pw, 52, c, rx=26) + circle(x + 26, y + 26, 19, WHITE) + text(x + 26, y + 33, lab, 18, 800, c, "middle")
        (tt,), tfs = fit(ttl, 18, pw - 80, 1, 700, 14)
        o += text(x + pw / 2 + 18, y + 26 + tfs * 0.36, tt, tfs, 700, WHITE, "middle")
    o += dotted(lx + pw + 6, y + 26, rx_ - 6, y + 26, NAVY)
    y += 74
    rh = min(72, (BOT - y - 12 * (len(rows) - 1)) / max(len(rows), 1))
    for row in rows:
        q, a = (row.get("q", ""), row.get("a", "")) if isinstance(row, dict) else (row[0], row[1] if len(row) > 1 else "")
        o += rect(lx, y, pw, rh, LAV, rx=rh / 2) + rect(rx_, y, pw, rh, MINT_BG, rx=rh / 2)
        ql, qfs = fit(q, 17, pw - 56, 2, 600, 14)
        al, afs = fit(a, 16, pw - 56, 2, 400, 14)
        o += lines(lx + pw / 2, y + rh / 2, ql, qfs, 23, 600, NAVY, "middle", valign_center=True)
        o += lines(rx_ + pw / 2, y + rh / 2, al, afs, 22, 400, INK, "middle", valign_center=True)
        o += dotted(lx + pw + 6, y + rh / 2, rx_ - 6, y + rh / 2)
        y += rh + 12
    return o


# ── data layouts ─────────────────────────────────────────────────────────────

def chart(p):
    """Line or bar chart + up to 3 key points (template p.5). labels[], values[], kind: line|bar."""
    labels, vals = p.get("labels", []), [float(v) for v in p.get("values", [])]
    kind = p.get("kind", "line")
    pts = items(p, "points", 0, 3) if p.get("points") else []
    x0, x1 = L + 56, R - 24
    y0, y1 = TOP + 18, (408 if pts else BOT - 34)
    vmax = p.get("max") or nice_max(max(vals) * 1.12 if vals else 1)
    nt = 5
    o = ""
    for k in range(nt + 1):
        yy = y1 - (y1 - y0) * k / nt
        o += line(x0, yy, x1, yy, LINE, 1)
        o += text(x0 - 10, yy + 5, f"{vmax * k / nt:.0f}", 13, 500, MUTED, "end")
    n = len(vals)
    step = (x1 - x0) / max(n, 1)
    xy = []
    hl = p.get("highlight", n - 1)
    unit = p.get("unit", "")
    for i, v in enumerate(vals):
        cx = x0 + step * (i + 0.5)
        cy = y1 - (y1 - y0) * v / vmax
        xy.append((cx, cy))
        if kind == "bar":
            bw = min(56, step * 0.5)
            o += rect(cx - bw / 2, cy, bw, y1 - cy, NAVY if i == hl else GREEN, rx=4)
        o += text(cx, y1 + 22, str(labels[i]) if i < len(labels) else "", 14, 600, BODY, "middle")
    if kind != "bar" and xy:
        o += path("M" + " L".join(f"{r1(a)},{r1(b)}" for a, b in xy), stroke=NAVY, sw=3)
        for i, (a, b) in enumerate(xy):
            o += circle(a, b, 6 if i == hl else 4.5, GREEN if i == hl else NAVY)
    for i, (a, b) in enumerate(xy):
        v = vals[i]
        o += text(a, b - 14, f"{v:g}{unit}", 18 if i == hl else 16, 700, GREEN if i == hl else NAVY, "middle")
    if pts:
        w = CONTENT_W / len(pts)
        for i, it in enumerate(pts):
            cxi = L + w * (i + 0.5)
            c = [GREEN, TEAL, NAVY][i]
            o += text(cxi, 470, fit(it["title"], 19, w - 30, 1, 700, 15)[0][0], 19, 700, c, "middle")
            if it.get("desc"):
                dl, dfs = fit(it["desc"], 15, w - 36, 2, 400, 13)
                o += lines(cxi, 498, dl, dfs, 22, 400, BODY, "middle")
    if p.get("source"):
        o += text(R, BOT + 8, p["source"], 12, 400, MUTED, "end")
    return o


def table(p):
    """Header row + up to 6 rows; optional highlight column (template p.12)."""
    head = p.get("header", [])
    rows = (p.get("rows") or [])[:6]
    nc = len(head)
    if not nc:
        warn("table: 'header' is required")
        return ""
    weights = [max(measure(str(r_[j]) if j < len(r_) else "", 15) for r_ in rows + [head]) + 40 for j in range(nc)]
    tw = CONTENT_W - 24
    ws = [w * tw / sum(weights) for w in weights]
    x0 = L + 12
    rh = min(54, (BOT - TOP - 54) / max(len(rows), 1))
    y = vcenter(50 + rh * len(rows))
    hl = p.get("highlight_col")
    o = rect(x0, y, tw, 50 + rh * len(rows), WHITE, rx=14, stroke=LINE, sw=1)
    o += rect(x0, y, tw, 50, NAVY, rx=14) + rect(x0, y + 30, tw, 20, NAVY)
    xs = [x0 + sum(ws[:j]) for j in range(nc)]
    if hl is not None and 0 <= hl < nc:
        o += rect(xs[hl], y + 50, ws[hl], rh * len(rows) - 10, MINT_PALE)
        o += rect(xs[hl], y + 50 + rh * len(rows) - 14, ws[hl], 14, MINT_PALE, rx=10)
    for j, hdr in enumerate(head):
        (hh,), hfs = fit(str(hdr), 16, ws[j] - 20, 1, 700, 13)
        o += text(xs[j] + ws[j] / 2, y + 31, hh, hfs, 700, WHITE, "middle")
    yy = y + 50
    for i, r_ in enumerate(rows):
        if i:
            o += line(x0, yy, x0 + tw, yy, LINE, 1)
        for j in range(nc):
            cell = str(r_[j]) if j < len(r_) else ""
            cl, cfs = fit(cell, 15, ws[j] - 20, 2, 400, 13)
            o += lines(xs[j] + ws[j] / 2, yy + rh / 2, cl, cfs, 20, 600 if j == 0 else 400, INK, "middle",
                       valign_center=True)
        yy += rh
    for j in range(1, nc):
        o += line(xs[j], y + 50, xs[j], yy, LINE, 1)
    return o


def image(p):
    """User image / screenshot (rounded) + up to 3 points on the right."""
    src = p.get("_image_href")
    pts = items(p, "points", 0, 3) if p.get("points") else []
    iw = 470 if pts else CONTENT_W - 60
    ix = L + 12 if pts else CX - iw / 2
    iy, ih = TOP + 6, BOT - TOP - 16
    cid = f"clip{abs(hash(src)) % 10000}"
    o = rect(ix - 6, iy - 6, iw + 12, ih + 12, MINT_BG, rx=20)
    if src:
        o += (f'  <defs><clipPath id="{cid}"><rect x="{r1(ix)}" y="{r1(iy)}" width="{r1(iw)}" height="{r1(ih)}" rx="14"/>'
              f'</clipPath></defs>\n  <image href="{esc(src)}" x="{r1(ix)}" y="{r1(iy)}" width="{r1(iw)}" height="{r1(ih)}" '
              f'preserveAspectRatio="xMidYMid {"slice" if p.get("fit") == "cover" else "meet"}" clip-path="url(#{cid})"/>\n')
    else:
        warn("image layout without 'src' — an empty frame was drawn")
    if p.get("caption"):
        o += text(ix + iw / 2, BOT + 6, p["caption"], 13, 400, MUTED, "middle")
    if pts:
        x = ix + iw + 34
        w = R - x
        y = vcenter(len(pts) * 100) + 10
        for i, it in enumerate(pts):
            c = [GREEN, TEAL, NAVY][i]
            o += rect(x, y, 4, 70, c, rx=2)
            o += text(x + 18, y + 22, fit(it["title"], 19, w - 20, 1, 700, 15)[0][0], 19, 700, c)
            if it.get("desc"):
                dl, dfs = fit(it["desc"], 15, w - 20, 2, 400, 13)
                o += lines(x + 18, y + 48, dl, dfs, 22, 400, BODY)
            y += 100
    return o


# ── lecture-deck layouts (quiz · bullets · panels · grid · keywords) ─────────

def stamp(lines_, cx, cy, fs=24, angle=-6):
    """Tilted penalty stamp (navy frame, green bold text) — for 벌칙·과태료 callouts."""
    w = max(measure(s_, fs, 800) for s_ in lines_) + 56
    h = len(lines_) * fs * 1.25 + 30
    o = rect(cx - w / 2, cy - h / 2, w, h, WHITE, rx=6, stroke=NAVY, sw=4)
    o += lines(cx, cy, lines_, fs, fs * 1.25, 800, GREEN, "middle", valign_center=True)
    return f'  <g transform="rotate({angle} {r1(cx)} {r1(cy)})">\n{o}  </g>\n'


def _marker(kind, x, y):
    if kind == "diamond":
        return poly([(x, y - 6), (x + 6, y), (x, y + 6), (x - 6, y)], NAVY)
    if kind == "check":
        return path(f"M{r1(x - 6)},{r1(y)} L{r1(x - 1)},{r1(y + 5)} L{r1(x + 7)},{r1(y - 5)}", stroke=GREEN, sw=3)
    return circle(x, y, 4.5, GREEN)


def _label_line(x, y, s_, fs, fw, fill, maxw, lh, sep=":"):
    """'라벨 : 내용' → bold navy label + body text in one text box; wraps to 2 lines, label kept on line 1."""
    ls_, f2 = fit(s_, fs, maxw, 2, fw, 14)
    o = ""
    for i, ln_ in enumerate(ls_):
        yy = y + i * lh
        if i == 0 and sep in ln_:
            a, b = ln_.split(sep, 1)
            o += (f'  <text x="{r1(x)}" y="{r1(yy)}" font-family="{prim.FONT}" font-size="{f2}" font-weight="700" '
                  f'fill="{NAVY}">{esc(a + sep)}<tspan font-weight="{fw}" fill="{fill}">{esc(b)}</tspan></text>\n')
        else:
            o += text(x, yy, ln_, f2, fw, fill)
    return o, len(ls_)


def bullets(p):
    """Bullet list (dot · diamond · check) with optional heading, footnote, stamp and illustration.
    Type size follows the item count (22 → 18px) unless `size` is given; rows spread to fill the area."""
    its = items(p, lo=1, hi=8)
    has_ill = p.get("illust", "auto") != "none"
    x = L + 20
    w = 476 if has_ill else 730
    marker = p.get("marker", "dot")
    n = len(its)
    fs = p.get("size") or {1: 22, 2: 22, 3: 22, 4: 22, 5: 21, 6: 20}.get(n, 18)
    o = ""
    top = TOP + 6
    if p.get("heading"):
        (hd,), hfs = fit(p["heading"], 21, w, 1, 700, 16)
        o += rect(x - 4, top + 2, 5, 26, GREEN, rx=2) + text(x + 12, top + 23, hd, hfs, 700, NAVY)
        top += 52
    bot = BOT - (34 if p.get("note") else 0)
    lh = round(fs * 1.4)
    rows = [len(wrap(it["title"], fs, w - 28, 500)) for it in its]
    text_h = sum(min(r_, 2) * lh for r_ in rows)
    gap = max(12, min(34, (bot - top - text_h - 20) / max(n - 1, 1)))
    total = text_h + gap * (n - 1)
    y = vcenter(total, top, bot) + fs * 0.85
    for it in its:
        o += _marker(marker, x + 6, y - fs * 0.34)
        if p.get("label_split", True):
            svg, k = _label_line(x + 26, y, it["title"], fs, 500, INK, w - 28, lh)
        else:
            ls_, f2 = fit(it["title"], fs, w - 28, 2, 500, 14)
            svg, k = lines(x + 26, y, ls_, f2, lh, 500, INK), len(ls_)
        o += svg
        y += k * lh + gap
    if p.get("note"):
        o += text(x, BOT - 4, p["note"], 15, 500, BODY)
    if p.get("stamp"):
        o += stamp(p["stamp"], *(p.get("stamp_at") or (640, 430)))
    if has_ill:
        o += ill(p, 568, 196, 272, 330, "auto")
    return o


def panels(p):
    """Headed text boxes stacked (cols: 1) or side by side (cols: 2).
    panels: [{heading, lines: [...], items: [...], note}]"""
    pans = p.get("panels") or []
    cols = p.get("cols", 1)
    has_ill = p.get("illust", "none") != "none" and cols == 1
    W_ = 476 if has_ill else CONTENT_W - 24
    o = ""
    fs, lh = 16, 24

    def body(pn, w):
        rows = []
        for s_ in pn.get("lines") or []:
            rows += [("t", ln_) for ln_ in wrap(s_, fs, w - 40, 400)]
        for s_ in pn.get("items") or []:
            rows += [("b" if j == 0 else "c", ln_) for j, ln_ in enumerate(wrap(s_, fs, w - 58, 400))]
        if pn.get("note"):
            rows.append(("n", pn["note"]))
        return rows

    def height(pn, rows):
        return (36 if pn.get("heading") else 0) + len(rows) * lh + 26

    def draw(pn, x, y, w, rows):
        q = ""
        if pn.get("heading"):
            (hd,), hfs = fit(pn["heading"], 19, w - 40, 1, 700, 14)
            q += check_mark(x + 12, y + 13, 11, GREEN, WHITE) + text(x + 32, y + 20, hd, hfs, 700, NAVY)
            y += 36
        bh = len(rows) * lh + 26
        q += rect(x, y, w, bh, MINT_PALE, rx=14)
        yy = y + 13 + fs
        for kind, s_ in rows:
            if kind == "b":
                q += circle(x + 26, yy - fs * 0.34, 3.5, GREEN)
            xx = x + (38 if kind in "bc" else 20)
            q += text(xx, yy, s_, fs, 600 if kind == "n" else 400, TEAL if kind == "n" else INK)
            yy += lh
        return q

    def total_h(size):
        nonlocal fs, lh
        fs, lh = size, round(size * 1.5)
        if cols == 2:
            w = (W_ - 20) / 2
            return max(height(pn, body(pn, w)) for pn in pans[:2])
        return sum(height(pn, body(pn, W_)) for pn in pans) + 22 * (len(pans) - 1)

    if p.get("size"):
        total_h(p["size"])
    else:                                   # largest size (19 → 15) that fits the content area
        for size in (19, 18, 17, 16, 15):
            if total_h(size) <= BOT - TOP - 10:
                break
    if cols == 2:
        w = (W_ - 20) / 2
        bodies = [body(pn, w) for pn in pans[:2]]
        y0 = vcenter(max(height(pn, b_) for pn, b_ in zip(pans, bodies)))
        for i, (pn, b_) in enumerate(zip(pans, bodies)):
            o += draw(pn, L + 12 + i * (w + 20), y0, w, b_)
    else:
        bodies = [body(pn, W_) for pn in pans]
        hs = [height(pn, b_) for pn, b_ in zip(pans, bodies)]
        gap = 22
        total = sum(hs) + gap * (len(hs) - 1)
        if total > BOT - TOP:
            warn(f"panels: content is {total:.0f}px tall (> {BOT - TOP}) — reduce lines or size")
        y = vcenter(total)
        for pn, b_, hh in zip(pans, bodies, hs):
            o += draw(pn, L + 12, y, W_, b_)
            y += hh + gap
    if p.get("stamp"):
        o += stamp(p["stamp"], *(p.get("stamp_at") or (600, 470)))
    if has_ill:
        o += ill(p, 568, 196, 272, 330, "auto")
    return o


def grid(p):
    """Up to 6 tiles (3 × 2): no, title, desc."""
    its = items(p, lo=2, hi=6)
    n = len(its)
    cols = 3 if n in (3, 5, 6) else 2
    rows_ = (n + cols - 1) // cols
    gap = 16
    w = (CONTENT_W - 24 - gap * (cols - 1)) / cols
    h = min(200, (BOT - TOP - 6 - gap * (rows_ - 1)) / rows_)
    y0 = vcenter(rows_ * h + gap * (rows_ - 1))
    o = ""
    for i, it in enumerate(its):
        x, y = L + 12 + (i % cols) * (w + gap), y0 + (i // cols) * (h + gap)
        c = [GREEN, TEAL, NAVY][i % 3]
        o += rect(x, y, w, h, MINT_PALE, rx=16) + rect(x + 20, y + 18, 26, 4, c, rx=2)
        yy = y + 18
        if it.get("no"):
            o += text(x + 20, yy + 26, str(it["no"]), 17, 700, c)
            yy += 26
        tl, tfs = fit(it["title"], 21, w - 40, 1, 800, 16)
        o += text(x + 20, yy + 30, tl[0], tfs, 800, NAVY)
        if it.get("desc"):
            dl, dfs = fit(it["desc"], 15, w - 40, 3, 400, 13)
            o += lines(x + 20, yy + 58, dl, dfs, 22, 400, BODY)
    return o


def keywords(p):
    """Definition box + keyword chips (+ illustration)."""
    o = ""
    d = p.get("definition") or {}
    y = TOP + 6
    if d:
        hl = fit(d["heading"], 17, CONTENT_W - 64, 1, 700, 14)[0] if d.get("heading") else []
        tl, tfs = fit(d.get("text", ""), 20, CONTENT_W - 64, 2, 700, 16)
        bh = 26 + len(hl) * 28 + len(tl) * 30 + 8
        o += rect(L + 12, y, CONTENT_W - 24, bh, NAVY, rx=16)
        yy = y + 36
        for s_ in hl:
            o += text(L + 36, yy, s_, 17, 600, MINT)
            yy += 30
        o += lines(L + 36, yy, tl, tfs, 30, 700, WHITE)
        y += bh + 28
    chips = [c if isinstance(c, str) else c.get("title", "") for c in (p.get("chips") or [])]
    has_ill = p.get("illust", "auto") != "none"
    maxx = 560 if has_ill else R - 12
    x = L + 12
    ch, gap = 44, 12
    y0 = y
    for i, c in enumerate(chips):
        w = measure(c, 18, 700) + 40
        if x + w > maxx:
            x = L + 12
            y += ch + gap
        o += rect(x, y, w, ch, [MINT_BG, LAV, MINT_PALE][i % 3], rx=ch / 2) + text(x + w / 2, y + 29, c, 18, 700, NAVY, "middle")
        x += w + gap
    if has_ill:
        o += ill(p, 580, y0 - 10, 260, BOT - y0 + 10, "auto")
    return o


def quiz(p):
    """Quiz: question bar + options (answer highlighted) or an O/X reveal.
    question, options[], answer (1-based — reveal page only), reveal ('X' / 'O'), explain, illust."""
    o = ""
    qx, qw = L + 12, CONTENT_W - 24
    ql, qfs = fit(p.get("question", ""), 21, qw - 60, 3, 700, 16)
    qh = max(80, len(ql) * 30 + 34)
    qy = TOP + 2
    o += rect(qx, qy, qw, qh, WHITE, rx=20, stroke=GREEN, sw=3)
    o += lines(qx + 30, qy + qh / 2, ql, qfs, 30, 700, NAVY, valign_center=True)
    ay = qy + qh + 18
    has_ill = p.get("illust", "thinking") != "none"
    ax = L + 228 if has_ill else qx
    aw, ah = R - 12 - ax, BOT - ay
    if has_ill:
        o += ill(p, L + 4, ay + 10, 210, ah - 20, "thinking")
    opts = p.get("options") or []
    ans = p.get("answer")
    if opts:
        n = len(opts)
        gap = 10
        rh = (ah - gap * (n - 1)) / n
        for i, op_ in enumerate(opts):
            y = ay + i * (rh + gap)
            hit = ans == i + 1
            head, _, rest = op_.partition(" ")
            num, body_ = (head, rest) if head.rstrip(".").isdigit() else ("", op_)
            o += rect(ax, y, aw, rh, GREEN if hit else MINT_PALE, rx=14)
            if num:
                o += text(ax + 22, y + rh / 2 + 6, num, 18, 800, WHITE if hit else GREEN)
            bl, bfs = fit(body_, 17, aw - 110, 2, 700 if hit else 500, 14)
            o += lines(ax + 56, y + rh / 2, bl, bfs, 23, 700 if hit else 500, WHITE if hit else INK, valign_center=True)
            if hit:
                o += check_mark(ax + aw - 30, y + rh / 2, 13, WHITE, GREEN)
    else:
        o += rect(ax, ay, aw, ah, MINT_PALE, rx=20)
        if p.get("reveal"):
            o += text(ax + aw / 2, ay + ah / 2 + (14 if p.get("explain") else 42), p["reveal"], 120, 900, NAVY, "middle")
        if p.get("explain"):
            el, efs = fit(p["explain"], 24, aw - 40, 2, 800, 18)
            o += lines(ax + aw / 2, ay + ah - 40, el, efs, 32, 800, GREEN, "middle")
    return o


LAYOUTS = {
    # name: (function, needs_gm, file-role)
    "cover": (cover, False, "cover"),
    "agenda": (agenda, False, "chapter"),
    "section": (section, False, "chapter"),
    "statement": (statement, True, "content"),
    "points": (points, True, "content"),
    "icon_list": (icon_list, True, "content"),
    "cards": (cards, True, "content"),
    "stats": (stats, True, "content"),
    "illust_cards": (illust_cards, True, "content"),
    "flow": (flow, True, "content"),
    "compare": (compare, True, "content"),
    "before_after": (before_after, True, "content"),
    "pyramid": (pyramid, True, "content"),
    "hub": (hub, True, "content"),
    "qa": (qa, True, "content"),
    "chart": (chart, True, "content"),
    "table": (table, True, "content"),
    "image": (image, True, "content"),
    "bullets": (bullets, True, "content"),
    "panels": (panels, True, "content"),
    "grid": (grid, True, "content"),
    "keywords": (keywords, True, "content"),
    "quiz": (quiz, True, "content"),
    "ending": (ending, False, "ending"),
}

# layouts whose title sits in the shell (others draw their own headline)
SHELL_TITLE = {"bullets", "panels", "grid", "keywords", "quiz", "agenda", "statement", "points", "cards", "stats", "illust_cards", "flow", "compare", "before_after",
               "pyramid", "qa", "chart", "table", "image"}
