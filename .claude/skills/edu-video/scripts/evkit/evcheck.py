"""evkit.evcheck — edu-video zone + accessibility gate for svg_output pages.

Rules (design-system.md §2, §4):
  Z1  nothing may cross x > 872 (24px gutter before the instructor stage at x 896)
  Z2  nothing may enter the caption safe zone y > 644
  A1  no <text> below 28px
The stage tint rect (id="stage") and the full-canvas background are exempt.
"""
import re

import ev

NUM = re.compile(r"-?\d*\.?\d+")


def _attrs(tag):
    return dict(re.findall(r'([\w:-]+)="([^"]*)"', tag))


def _f(a, k, d=0.0):
    try:
        return float(a.get(k, d))
    except ValueError:
        return d


def boxes(svg):
    """Yield (kind, x0, y0, x1, y1, info) for every drawable element."""
    for m in re.finditer(r"<(rect|circle|line|path|use|image|text)\b([^>]*)>(?:(.*?)</text>)?", svg, re.S):
        kind, raw, inner = m.group(1), m.group(2), m.group(3) or ""
        a = _attrs(raw)
        if a.get("id") == "stage":
            continue
        if kind == "rect":
            x, y, w, h = _f(a, "x"), _f(a, "y"), _f(a, "width"), _f(a, "height")
            if w >= ev.W and h >= ev.H:
                continue
            yield kind, x, y, x + w, y + h, ""
        elif kind == "circle":
            cx, cy, rr = _f(a, "cx"), _f(a, "cy"), _f(a, "r")
            yield kind, cx - rr, cy - rr, cx + rr, cy + rr, ""
        elif kind == "line":
            xs, ys = (_f(a, "x1"), _f(a, "x2")), (_f(a, "y1"), _f(a, "y2"))
            yield kind, min(xs), min(ys), max(xs), max(ys), ""
        elif kind == "path":
            nums = [float(n) for n in NUM.findall(re.sub(r"[A-Za-z]", " ", a.get("d", "")))]
            xs, ys = nums[0::2], nums[1::2]
            if xs and ys:
                yield kind, min(xs), min(ys), max(xs), max(ys), ""
        elif kind in ("use", "image"):
            x, y, w, h = _f(a, "x"), _f(a, "y"), _f(a, "width"), _f(a, "height")
            yield kind, x, y, x + w, y + h, a.get("data-icon", a.get("href", ""))
        elif kind == "text":
            x, y, fs = _f(a, "x"), _f(a, "y"), _f(a, "font-size", 16)
            txt = re.sub(r"<[^>]+>", "", inner).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            w = ev.text_w(txt, fs, a.get("font-weight") in ("700", "800"))
            anc = a.get("text-anchor", "start")
            x0 = x - w / 2 if anc == "middle" else (x - w if anc == "end" else x)
            yield kind, x0, y - fs * 0.8, x0 + w, y + fs * 0.25, (fs, txt)


def check_svg(svg, name=""):
    errs = []
    for kind, x0, y0, x1, y1, info in boxes(svg):
        label = f"{kind} {info[1][:24]!r}" if kind == "text" else kind
        if x1 > ev.SAFE_X + 0.6:
            errs.append(f"{name}: Z1 {label} reaches x={round(x1)} (> {ev.SAFE_X}, instructor stage)")
        if y1 > ev.CAPTION_Y + 0.6:
            errs.append(f"{name}: Z2 {label} reaches y={round(y1)} (> {ev.CAPTION_Y}, caption safe zone)")
        if kind == "text" and info[0] < ev.MIN_FS:
            errs.append(f"{name}: A1 text {info[0]}px < {ev.MIN_FS}px: {info[1][:30]!r}")
    return errs
