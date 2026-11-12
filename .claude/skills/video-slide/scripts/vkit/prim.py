"""vkit.prim — SVG primitives, text measurement and wrapping.

Everything returns SVG fragment strings. Text is always escaped here, so callers pass raw strings.
Width measurement uses the slide engine's Pretendard advance table (font_metrics.json) so wrapping
matches what PowerPoint will draw.
"""
import os
import sys
from pathlib import Path

from tokens import FONT, INK

ROOT = Path(__file__).resolve().parents[5]            # vkit→scripts→video-slide→skills→.claude→repo
ICON_DIR = ROOT / "assets" / "icons" / "tabler-outline"
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "slide" / "scripts" / "svg_to_pptx"))
try:
    import font_metrics as _fm                         # noqa: E402
except Exception:                                      # pragma: no cover - engine missing
    _fm = None

WARNINGS = []
LOCK = False          # content-lock mode: layouts add no decorative text (brackets, labels, numbers)


def deco(s, left="「 ", right=" 」"):
    """Decorative wrapper around existing text — dropped in content-lock mode."""
    return s if LOCK else f"{left}{s}{right}"


def warn(msg):
    WARNINGS.append(msg)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


# ── measurement + wrapping ───────────────────────────────────────────────────

def measure(s, fs, fw=400):
    """Rendered width in px (Pretendard advances; falls back to an estimate)."""
    s = str(s)
    if _fm is not None:
        try:
            w = _fm.measure_text(s, fs, str(fw))
            if w is not None:
                return w * (1.03 if fw >= 700 else 1.0)
        except Exception:
            pass
    return sum(fs * (0.88 if ord(c) > 0x1100 else 0.3 if c == " " else 0.58) for c in s)


def wrap(s, fs, maxw, fw=400):
    """Greedy word wrap on spaces; a word wider than maxw is broken by characters.
    Explicit '\\n' in the input forces a break."""
    out = []
    for para in str(s).split("\n"):
        line = ""
        for word in para.split(" "):
            cand = word if not line else line + " " + word
            if measure(cand, fs, fw) <= maxw:
                line = cand
                continue
            if line:
                out.append(line)
            line = ""
            while measure(word, fs, fw) > maxw:          # hard-break an over-long word
                k = len(word)
                while k > 1 and measure(word[:k], fs, fw) > maxw:
                    k -= 1
                out.append(word[:k])
                word = word[k:]
            line = word
        out.append(line)
    return out


def fit(s, fs, maxw, max_lines, fw=400, min_fs=None):
    """Wrap s into ≤ max_lines at the largest size between fs and min_fs. Returns (lines, fs).
    If it still does not fit, the last line is kept and a warning is recorded."""
    min_fs = min_fs or fs
    size = fs
    while True:
        lines = wrap(s, size, maxw, fw)
        if len(lines) <= max_lines or size <= min_fs:
            break
        size = round(size - 1, 1)
    if len(lines) > max_lines:
        warn(f"text too long for its box ({len(lines)} lines > {max_lines}): '{str(s)[:40]}…' — shorten it")
    return lines, size


# ── shapes ───────────────────────────────────────────────────────────────────

def _op(op, key="fill-opacity"):
    return f' {key}="{op}"' if op is not None else ""


def rect(x, y, w, h, fill, rx=None, op=None, stroke=None, sw=None, dash=None):
    a = f' rx="{rx}"' if rx else ""
    s = f' stroke="{stroke}" stroke-width="{sw or 1}"' if stroke else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'  <rect x="{r1(x)}" y="{r1(y)}" width="{r1(w)}" height="{r1(h)}" fill="{fill}"{a}{_op(op)}{s}{d}/>\n'


def circle(cx, cy, r, fill, op=None, stroke=None, sw=None):
    s = f' stroke="{stroke}" stroke-width="{sw or 1}"' if stroke else ""
    return f'  <circle cx="{r1(cx)}" cy="{r1(cy)}" r="{r1(r)}" fill="{fill}"{_op(op)}{s}/>\n'


def path(d, fill="none", stroke=None, sw=None, cap="round", join="round", op=None, dash=None):
    s = (f' stroke="{stroke}" stroke-width="{sw or 2}" stroke-linecap="{cap}" stroke-linejoin="{join}"'
         if stroke else "")
    dd = f' stroke-dasharray="{dash}"' if dash else ""
    return f'  <path d="{d}" fill="{fill}"{s}{dd}{_op(op)}/>\n'


def line(x1, y1, x2, y2, stroke, sw=1, dash=None, cap=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    c = f' stroke-linecap="{cap}"' if cap else ""
    return f'  <line x1="{r1(x1)}" y1="{r1(y1)}" x2="{r1(x2)}" y2="{r1(y2)}" stroke="{stroke}" stroke-width="{sw}"{d}{c}/>\n'


def poly(points, fill):
    pts = " ".join(f"{r1(x)},{r1(y)}" for x, y in points)
    return f'  <polygon points="{pts}" fill="{fill}"/>\n'


def r1(v):
    v = round(float(v), 1)
    return int(v) if v == int(v) else v


# ── text ─────────────────────────────────────────────────────────────────────

def text(x, y, s, fs, fw=400, fill=INK, anchor=None, ls=None, op=None):
    a = f' text-anchor="{anchor}"' if anchor and anchor != "start" else ""
    l = f' letter-spacing="{ls}"' if ls is not None else ""
    return (f'  <text x="{r1(x)}" y="{r1(y)}" font-family="{FONT}" font-size="{fs}" font-weight="{fw}"'
            f'{l}{a} fill="{fill}"{_op(op)}>{esc(s)}</text>\n')


def lines(x, y, ls_, fs, lh, fw=400, fill=INK, anchor=None, valign_center=False):
    """Draw a list of lines. y is the first baseline, or the visual centre if valign_center."""
    if valign_center:
        y = y - (len(ls_) - 1) * lh / 2 + fs * 0.35
    return "".join(text(x, y + i * lh, s, fs, fw, fill, anchor) for i, s in enumerate(ls_))


def block(x, y, s, fs, maxw, max_lines, lh=None, fw=400, fill=INK, anchor=None, min_fs=None, center=False):
    """Wrap-and-draw helper. Returns (svg, n_lines, used_fs, height)."""
    ls_, size = fit(s, fs, maxw, max_lines, fw, min_fs)
    lh = lh or round(size * 1.5, 1)
    return lines(x, y, ls_, size, lh, fw, fill, anchor, center), len(ls_), size, len(ls_) * lh


def split_two_tone(s):
    """'초록 부분 | 네이비 부분' → (초록, 네이비); no '|' → ("", all) in the second colour."""
    if "|" in s:
        a, b = s.split("|", 1)
        return a.strip(), b.strip()
    return "", s.strip()


def _joiner(s):
    """'A | B' keeps a space between the parts, 'A|B' joins them (e.g. '개인정보|란?')."""
    if "|" not in s:
        return " "
    a, b = s.split("|", 1)
    return " " if (a.endswith(" ") or b.startswith(" ")) else ""


def two_tone(x, y, s, fs, c1, c2, fw=800, anchor="middle", ls=None):
    """One <text> with a coloured <tspan> — stays one editable text box in PowerPoint."""
    a, b = split_two_tone(s)
    l = f' letter-spacing="{ls}"' if ls is not None else ""
    an = f' text-anchor="{anchor}"' if anchor and anchor != "start" else ""
    if not a:
        inner = esc(b)
        fill = c2
    else:
        inner = f'{esc(a)}{_joiner(s)}<tspan fill="{c2}">{esc(b)}</tspan>'
        fill = c1
    return (f'  <text x="{r1(x)}" y="{r1(y)}" font-family="{FONT}" font-size="{fs}" font-weight="{fw}"'
            f'{l}{an} fill="{fill}">{inner}</text>\n')


def plain(s):
    a, b = split_two_tone(s)
    return (a + _joiner(s) + b).strip() if a else b


# ── icons ────────────────────────────────────────────────────────────────────

def icon(name, x, y, s=28, color="#FFFFFF", sw=2):
    """Tabler outline icon (embedded by finalize_svg). Unknown names fall back to 'point'."""
    name = (name or "point").replace("tabler-outline/", "")
    if not (ICON_DIR / f"{name}.svg").exists():
        warn(f"icon '{name}' not found in assets/icons/tabler-outline — using 'point' "
             f"(search: grep <keyword> assets/icons/icons_index.txt)")
        name = "point"
    return (f'  <use data-icon="tabler-outline/{name}" x="{r1(x)}" y="{r1(y)}" width="{s}" height="{s}" '
            f'fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>\n')


def check_mark(cx, cy, r, bg, fg):
    """Check-in-circle drawn as native shapes (used by the GM pill)."""
    s = r * 0.42
    return (circle(cx, cy, r, bg) +
            path(f"M{r1(cx - s)},{r1(cy + 0.05 * r)} L{r1(cx - 0.12 * r)},{r1(cy + s * 0.85)} "
                 f"L{r1(cx + s)},{r1(cy - s * 0.7)}", stroke=fg, sw=max(2.5, r * 0.22)))
