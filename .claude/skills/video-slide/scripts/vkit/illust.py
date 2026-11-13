"""vkit.illust — original flat-vector illustration library (native SVG shapes → editable PPT shapes).

Style contract (references/design-system.md §6):
  * palette colours only (NAVY GREEN TEAL MINT MINT_BG LAV WHITE + SKIN/SUN for illustrations)
  * flat fills, no outlines except thick round-cap strokes for arms / handles / symbols
  * faceless rounded people, a soft organic backdrop blob, 1–3 small sparkles
  * every drawing lives in a 200 × 160 box and is placed with place(name, x, y, w, h)

Add a new drawing: write `def _name(): return svg` in the 200 × 160 box, register it in LIB with a
Korean meaning + keywords, run `scripts/gallery.py` and look at the render.
"""
from prim import circle, path, poly, rect, r1, warn
from tokens import GREEN, LAV, MINT, MINT_BG, MINT_PALE, NAVY, SKIN, SKIN_2, SUN, TEAL, WHITE

BW, BH = 200, 160


# ── shared parts ─────────────────────────────────────────────────────────────

def blob(fill=MINT_BG, op=None):
    return path("M24,96 C14,58 44,24 92,20 C142,16 184,40 186,82 C188,122 156,146 106,148 "
                "C62,150 32,132 24,96 Z", fill=fill, op=op)


def sparkle(x, y, s, color):
    """Four-point star."""
    k = s * 0.28
    return path(f"M{r1(x)},{r1(y - s)} Q{r1(x + k)},{r1(y - k)} {r1(x + s)},{r1(y)} "
                f"Q{r1(x + k)},{r1(y + k)} {r1(x)},{r1(y + s)} Q{r1(x - k)},{r1(y + k)} {r1(x - s)},{r1(y)} "
                f"Q{r1(x - k)},{r1(y - k)} {r1(x)},{r1(y - s)} Z", fill=color)


def leaf(x, y, w, h, color, flip=False):
    sx = -1 if flip else 1
    return path(f"M{r1(x)},{r1(y)} C{r1(x + sx * w * 0.9)},{r1(y - h * 0.2)} {r1(x + sx * w)},{r1(y - h * 0.8)} "
                f"{r1(x + sx * w * 0.3)},{r1(y - h)} C{r1(x - sx * w * 0.2)},{r1(y - h * 0.6)} "
                f"{r1(x - sx * w * 0.05)},{r1(y - h * 0.2)} {r1(x)},{r1(y)} Z", fill=color)


def plant(x, base_y, s=1.0):
    """Small potted plant; x = pot centre."""
    o = leaf(x, base_y - 16 * s, 16 * s, 34 * s, GREEN, flip=True)
    o += leaf(x, base_y - 16 * s, 18 * s, 40 * s, TEAL)
    o += leaf(x + 2 * s, base_y - 18 * s, 10 * s, 24 * s, MINT)
    o += path(f"M{r1(x - 12 * s)},{r1(base_y - 18 * s)} H{r1(x + 12 * s)} L{r1(x + 9 * s)},{r1(base_y)} "
              f"H{r1(x - 9 * s)} Z", fill=NAVY)
    return o


def person(cx, cy, r, shirt, hair="short", hair_color=NAVY, bottom=None, collar=True):
    """Faceless bust: head centre (cx, cy), head radius r; torso runs to `bottom`."""
    sy = cy + 1.3 * r
    bottom = bottom if bottom is not None else cy + 3.3 * r
    o = ""
    if hair == "long":
        o += rect(cx - 1.12 * r, cy - 1.1 * r, 2.24 * r, 2.25 * r, hair_color, rx=1.1 * r)
    o += rect(cx - 0.34 * r, cy + 0.6 * r, 0.68 * r, 0.9 * r, SKIN_2)                      # neck
    o += path(f"M{r1(cx - 1.75 * r)},{r1(bottom)} L{r1(cx - 1.75 * r)},{r1(sy + 0.85 * r)} "
              f"Q{r1(cx - 1.75 * r)},{r1(sy)} {r1(cx - 0.85 * r)},{r1(sy)} L{r1(cx + 0.85 * r)},{r1(sy)} "
              f"Q{r1(cx + 1.75 * r)},{r1(sy)} {r1(cx + 1.75 * r)},{r1(sy + 0.85 * r)} "
              f"L{r1(cx + 1.75 * r)},{r1(bottom)} Z", fill=shirt)                              # torso
    if collar:
        o += path(f"M{r1(cx - 0.42 * r)},{r1(sy)} L{r1(cx)},{r1(sy + 0.55 * r)} L{r1(cx + 0.42 * r)},{r1(sy)} Z",
                  fill=WHITE)
    o += circle(cx, cy, r, SKIN)                                                             # head
    hr = 1.06 * r
    if hair in ("short", "bun", "long"):
        o += path(f"M{r1(cx - hr)},{r1(cy + 0.05 * r)} A{r1(hr)},{r1(hr)} 0 0 1 {r1(cx + hr)},{r1(cy + 0.05 * r)} "
                  f"Q{r1(cx + 0.15 * r)},{r1(cy - 0.75 * r)} {r1(cx - 0.55 * r)},{r1(cy - 0.2 * r)} "
                  f"Q{r1(cx - 0.85 * r)},{r1(cy + 0.05 * r)} {r1(cx - hr)},{r1(cy + 0.05 * r)} Z", fill=hair_color)
    if hair == "bun":
        o += circle(cx + 0.15 * r, cy - 1.18 * r, 0.42 * r, hair_color)
    return o


def qmark(x, y, s, color, sw=None):
    """Question mark from strokes; (x, y) = top of the hook, s = size."""
    sw = sw or s * 0.32
    return (path(f"M{r1(x - s * 0.5)},{r1(y + s * 0.35)} C{r1(x - s * 0.5)},{r1(y - s * 0.25)} "
                 f"{r1(x + s * 0.5)},{r1(y - s * 0.25)} {r1(x + s * 0.5)},{r1(y + s * 0.3)} "
                 f"C{r1(x + s * 0.5)},{r1(y + s * 0.7)} {r1(x)},{r1(y + s * 0.7)} {r1(x)},{r1(y + s * 1.05)}",
                 stroke=color, sw=sw) + circle(x, y + s * 1.5, sw * 0.6, color))


def arrow_head(x, y, dx, dy, s, color):
    """Solid triangle pointing along (dx, dy) with its tip at (x, y)."""
    import math
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    bx, by = x - ux * s, y - uy * s
    return poly([(x, y), (bx - uy * s * 0.6, by + ux * s * 0.6), (bx + uy * s * 0.6, by - ux * s * 0.6)], color)


# ── drawings (200 × 160 box) ─────────────────────────────────────────────────

def _thinking():
    o = blob()
    o += person(96, 66, 20, GREEN, "short", bottom=152)
    o += path("M70,130 L114,130 L106,98", stroke=TEAL, sw=12)                                # folded arm
    o += circle(105, 93, 7, SKIN)                                                            # hand at chin
    o += qmark(150, 30, 18, NAVY)
    o += qmark(46, 44, 11, GREEN)
    o += sparkle(170, 92, 6, SUN) + circle(36, 100, 4, MINT)
    return o


def _presenter():
    o = blob()
    o += rect(18, 26, 116, 80, WHITE, rx=8) + rect(18, 26, 116, 12, NAVY, rx=6) + rect(18, 32, 116, 6, NAVY)
    o += rect(34, 76, 14, 18, MINT, rx=2) + rect(56, 64, 14, 30, GREEN, rx=2) + rect(78, 52, 14, 42, TEAL, rx=2)
    o += path("M34,64 L62,54 L84,44 L116,34", stroke=SUN, sw=4)
    o += path("M48,106 L40,140 M104,106 L112,140", stroke=NAVY, sw=4)
    o += person(158, 62, 15, NAVY, "bun", bottom=150)
    o += path("M146,96 C136,90 130,82 126,72", stroke=TEAL, sw=10)                          # pointing arm
    o += circle(125, 70, 5, SKIN)
    o += sparkle(182, 40, 6, SUN)
    return o


def _idea():
    o = blob()
    for x1, y1, x2, y2 in [(100, 14, 100, 4), (58, 30, 50, 22), (142, 30, 150, 22), (44, 66, 32, 66),
                           (156, 66, 168, 66)]:
        o += path(f"M{x1},{y1} L{x2},{y2}", stroke=GREEN, sw=5)
    o += circle(100, 66, 36, SUN)
    o += path("M86,92 Q100,104 114,92 L112,108 H88 Z", fill=SUN)
    o += path("M90,74 Q100,60 110,74 M100,72 L100,100", stroke=WHITE, sw=4)
    o += rect(86, 108, 28, 8, NAVY, rx=3) + rect(88, 118, 24, 8, NAVY, rx=3) + rect(94, 128, 12, 6, TEAL, rx=3)
    o += leaf(40, 140, 14, 32, GREEN) + leaf(40, 140, 12, 26, TEAL, flip=True)
    o += sparkle(160, 110, 8, MINT) + sparkle(48, 98, 5, NAVY)
    return o


def _team():
    o = blob()
    o += person(52, 72, 16, TEAL, "long", bottom=150)
    o += person(148, 72, 16, NAVY, "short", bottom=150)
    o += person(100, 58, 20, GREEN, "bun", bottom=150)
    o += sparkle(176, 34, 7, SUN) + sparkle(24, 40, 5, GREEN)
    return o


def _growth():
    o = blob()
    o += rect(30, 132, 140, 4, NAVY, rx=2)
    for i, (h, c) in enumerate([(26, MINT), (48, GREEN), (70, TEAL), (96, NAVY)]):
        o += rect(40 + i * 32, 132 - h, 22, h, c, rx=4)
    o += path("M36,96 L72,76 L100,84 L150,38", stroke=SUN, sw=6)
    o += arrow_head(162, 28, 12, -10, 16, SUN)
    o += circle(170, 112, 13, SUN) + circle(170, 112, 8, WHITE, op=0.6)
    o += sparkle(40, 40, 7, GREEN)
    return o


def _target():
    o = blob()
    for r, c in [(50, NAVY), (39, WHITE), (28, GREEN), (17, WHITE), (8, NAVY)]:
        o += circle(92, 86, r, c)
    o += path("M94,84 L154,30", stroke=TEAL, sw=5)
    o += poly([(154, 30), (172, 26), (164, 40)], TEAL) + poly([(150, 26), (158, 12), (162, 28)], MINT)
    o += path("M150,108 L150,144", stroke=NAVY, sw=4) + poly([(152, 108), (176, 116), (152, 124)], SUN)
    o += sparkle(34, 34, 7, SUN)
    return o


def _security():
    o = blob()
    o += rect(30, 40, 62, 82, WHITE, rx=6)
    for i in range(4):
        o += rect(40, 54 + i * 14, 42 - (i % 2) * 14, 5, MINT, rx=2)
    o += path("M110,20 L152,34 L152,74 C152,108 130,128 110,138 C90,128 68,108 68,74 L68,34 Z", fill=NAVY)
    o += path("M110,32 L142,43 L142,74 C142,100 126,116 110,125 C94,116 78,100 78,74 L78,43 Z", fill=GREEN)
    o += path("M100,74 L100,64 A10,10 0 0 1 120,64 L120,74", stroke=WHITE, sw=5)
    o += rect(94, 72, 32, 26, WHITE, rx=5) + circle(110, 83, 4, NAVY) + rect(108, 85, 4, 7, NAVY, rx=1)
    o += circle(160, 118, 13, SUN) + path("M154,118 L158,123 L167,113", stroke=WHITE, sw=3.5)
    o += sparkle(170, 30, 6, MINT)
    return o


def _checklist():
    o = blob()
    o += rect(54, 22, 92, 124, WHITE, rx=10) + rect(80, 14, 40, 16, NAVY, rx=6)
    for i, done in enumerate([True, True, False]):
        y = 48 + i * 30
        o += rect(68, y, 16, 16, GREEN if done else MINT_PALE, rx=4)
        if done:
            o += path(f"M71,{y + 8} L75,{y + 12} L81,{y + 4}", stroke=WHITE, sw=2.6)
        o += rect(92, y + 3, 40, 5, MINT, rx=2) + rect(92, y + 11, 26, 4, LAV, rx=2)
    o += path("M146,128 L176,72", stroke=SUN, sw=10, cap="butt") + poly([(141, 137), (144, 124), (151, 128)], NAVY)
    o += path("M173,77 L179,66", stroke=TEAL, sw=10, cap="round")
    o += sparkle(34, 44, 6, SUN)
    return o


def _chat():
    o = blob()
    o += rect(24, 30, 96, 60, NAVY, rx=16) + poly([(44, 86), (40, 106), (62, 88)], NAVY)
    for i in range(3):
        o += circle(52 + i * 20, 60, 5, WHITE)
    o += rect(84, 80, 96, 56, GREEN, rx=16) + poly([(160, 132), (166, 150), (146, 134)], GREEN)
    o += rect(100, 98, 60, 6, WHITE, rx=3) + rect(100, 112, 40, 6, WHITE, rx=3, op=0.7)
    o += sparkle(168, 44, 7, SUN) + circle(30, 120, 4, TEAL)
    return o


def _laptop():
    o = blob()
    o += rect(38, 34, 112, 74, NAVY, rx=8) + rect(46, 42, 96, 58, WHITE, rx=3)
    o += rect(52, 48, 40, 8, GREEN, rx=2) + rect(52, 62, 84, 5, MINT, rx=2) + rect(52, 72, 70, 5, MINT, rx=2)
    o += rect(52, 82, 26, 12, TEAL, rx=2) + rect(82, 82, 26, 12, MINT_PALE, rx=2)
    o += path("M26,108 H162 L154,120 H34 Z", fill=TEAL)
    o += plant(172, 120, 0.9)
    o += sparkle(30, 30, 6, SUN)
    return o


def _steps():
    o = blob()
    for i, c in enumerate([MINT, GREEN, TEAL, NAVY]):
        o += rect(30 + i * 34, 128 - (i + 1) * 22, 36, (i + 1) * 22, c, rx=3)
    o += path("M146,40 L146,8", stroke=NAVY, sw=4) + poly([(148, 8), (172, 16), (148, 26)], SUN)
    o += path("M40,92 L104,52", stroke=NAVY, sw=4, dash="2 8") + arrow_head(116, 44, 12, -8, 12, NAVY)
    o += sparkle(180, 52, 7, GREEN) + sparkle(30, 40, 5, SUN)
    return o


def _search():
    o = blob()
    o += rect(34, 24, 84, 108, WHITE, rx=8)
    for i, w in enumerate([56, 44, 60, 36, 50]):
        o += rect(46, 40 + i * 16, w, 6, MINT if i % 2 else LAV, rx=3)
    o += path("M136,110 L166,140", stroke=NAVY, sw=14)
    o += circle(118, 90, 30, NAVY) + circle(118, 90, 22, MINT_BG)
    o += path("M106,82 A14,14 0 0 1 120,74", stroke=WHITE, sw=4)
    o += sparkle(170, 40, 7, SUN)
    return o


def _book():
    o = blob()
    o += path("M100,52 C80,40 52,40 26,46 L26,128 C52,122 80,122 100,134 Z", fill=GREEN)
    o += path("M100,52 C120,40 148,40 174,46 L174,128 C148,122 120,122 100,134 Z", fill=TEAL)
    o += path("M100,56 C82,46 58,46 34,50 L34,120 C58,116 82,116 100,126 Z", fill=WHITE)
    o += path("M100,56 C118,46 142,46 166,50 L166,120 C142,116 118,116 100,126 Z", fill=MINT_PALE)
    for i in range(3):
        o += path(f"M46,{68 + i * 14} C60,{65 + i * 14} 74,{65 + i * 14} 88,{69 + i * 14}", stroke=MINT, sw=3)
        o += path(f"M112,{69 + i * 14} C126,{65 + i * 14} 140,{65 + i * 14} 154,{68 + i * 14}", stroke=MINT, sw=3)
    o += sparkle(100, 22, 9, SUN) + sparkle(64, 26, 5, NAVY) + sparkle(138, 26, 5, GREEN)
    return o


def _calendar():
    o = blob()
    o += rect(28, 32, 108, 100, WHITE, rx=10) + rect(28, 32, 108, 26, NAVY, rx=10) + rect(28, 46, 108, 12, NAVY)
    o += rect(50, 24, 6, 16, TEAL, rx=3) + rect(108, 24, 6, 16, TEAL, rx=3)
    for r_ in range(3):
        for c_ in range(4):
            hl = (r_, c_) == (1, 2)
            o += rect(38 + c_ * 24, 66 + r_ * 20, 18, 14, GREEN if hl else MINT_PALE, rx=3)
    o += circle(146, 112, 30, WHITE) + circle(146, 112, 30, "none", stroke=NAVY, sw=6)
    o += path("M146,96 L146,112 L158,120", stroke=GREEN, sw=5)
    o += sparkle(176, 50, 7, SUN)
    return o


def _trophy():
    o = blob()
    o += path("M70,48 C52,48 50,78 76,86", stroke=SUN, sw=8) + path("M130,48 C148,48 150,78 124,86", stroke=SUN, sw=8)
    o += path("M68,32 H132 V58 C132,84 116,98 100,98 C84,98 68,84 68,58 Z", fill=SUN)
    o += rect(92, 96, 16, 18, SUN) + rect(76, 112, 48, 12, NAVY, rx=4) + rect(66, 124, 68, 12, TEAL, rx=4)
    o += path("M88,46 L88,66", stroke=WHITE, sw=5, op=None)
    o += sparkle(40, 40, 8, GREEN) + sparkle(162, 36, 6, NAVY) + sparkle(156, 108, 8, MINT)
    o += rect(36, 96, 8, 8, GREEN, rx=1) + circle(166, 76, 4, TEAL)
    return o


def _puzzle():
    o = blob()
    pcs = [(48, 32, GREEN), (100, 32, NAVY), (48, 84, TEAL), (100, 84, MINT)]
    for x, y, c in pcs:
        o += rect(x, y, 50, 50, c, rx=6)
    o += circle(98, 57, 9, GREEN) + circle(125, 82, 9, NAVY)
    o += circle(73, 82, 9, GREEN) + circle(98, 109, 9, TEAL)
    o += sparkle(168, 40, 8, SUN) + sparkle(30, 124, 5, NAVY)
    return o


def _alert():
    o = blob()
    o += path("M100,22 C106,22 110,25 113,30 L164,118 C170,128 164,138 152,138 L48,138 "
              "C36,138 30,128 36,118 L87,30 C90,25 94,22 100,22 Z", fill=SUN)
    o += rect(93, 58, 14, 46, NAVY, rx=7) + circle(100, 120, 8, NAVY)
    o += path("M176,40 L186,32 M178,58 L190,58 M24,52 L14,46 M22,72 L10,74", stroke=TEAL, sw=4)
    return o


def _idcard():
    o = blob()
    o += rect(26, 34, 132, 92, WHITE, rx=10) + rect(26, 34, 132, 20, NAVY, rx=10) + rect(26, 44, 132, 10, NAVY)
    o += circle(62, 86, 20, MINT_BG) + circle(62, 80, 8, NAVY) + path("M48,100 Q62,86 76,100 Z", fill=NAVY)
    o += rect(92, 70, 52, 7, MINT, rx=3) + rect(92, 84, 40, 6, LAV, rx=3) + rect(92, 96, 46, 6, LAV, rx=3)
    o += circle(156, 120, 22, GREEN)
    o += path("M149,118 L149,111 A7,7 0 0 1 163,111 L163,118", stroke=WHITE, sw=3.5)
    o += rect(145, 116, 22, 16, WHITE, rx=3) + circle(156, 124, 2.6, GREEN)
    o += sparkle(178, 32, 6, SUN)
    return o


def _video():
    o = blob()
    o += rect(26, 30, 132, 88, NAVY, rx=12) + rect(34, 38, 116, 72, TEAL, rx=6)
    o += circle(92, 74, 20, WHITE) + poly([(86, 63), (86, 85), (104, 74)], GREEN)
    o += rect(34, 128, 116, 6, MINT, rx=3) + rect(34, 128, 48, 6, GREEN, rx=3) + circle(82, 131, 6, GREEN)
    o += sparkle(176, 40, 7, SUN) + circle(176, 100, 5, MINT)
    return o


def _goal():
    """Person reaching the summit flag — motivation / achievement."""
    o = blob()
    o += path("M14,146 L76,52 L110,96 L132,70 L188,146 Z", fill=TEAL)
    o += path("M76,52 L92,76 L84,72 L76,82 L66,70 Z", fill=WHITE)
    o += path("M14,146 L76,52 L64,146 Z", fill=NAVY, op=0.35)
    o += path("M76,52 L76,18", stroke=NAVY, sw=4) + poly([(78, 18), (102, 26), (78, 36)], SUN)
    o += sparkle(150, 40, 8, GREEN) + sparkle(32, 54, 5, SUN)
    return o


def _printer():
    o = blob()
    o += rect(62, 20, 76, 46, WHITE, rx=4)
    for i in range(3):
        o += rect(72, 30 + i * 10, 56 - i * 12, 4, MINT, rx=2)
    o += rect(34, 58, 132, 54, NAVY, rx=12) + rect(48, 94, 104, 30, TEAL, rx=6)
    o += rect(58, 104, 84, 34, WHITE, rx=3) + rect(66, 114, 50, 4, LAV, rx=2) + rect(66, 124, 36, 4, LAV, rx=2)
    o += circle(150, 72, 5, SUN) + rect(46, 70, 40, 6, WHITE, rx=3, op=0.35)
    o += sparkle(176, 34, 7, GREEN)
    return o


def _shredder():
    o = blob()
    o += rect(70, 16, 60, 52, WHITE, rx=4) + rect(80, 28, 40, 4, MINT, rx=2) + rect(80, 38, 30, 4, MINT, rx=2)
    o += rect(40, 60, 120, 30, NAVY, rx=10) + rect(62, 72, 76, 6, WHITE, rx=3, op=0.6)
    o += path("M46,90 H154 L146,144 H54 Z", fill=TEAL)
    for i in range(6):
        o += rect(70 + i * 11, 92, 5, 26 + (i % 3) * 6, WHITE, rx=2)
    o += circle(146, 75, 4, SUN)
    o += sparkle(176, 40, 7, GREEN) + sparkle(28, 50, 5, SUN)
    return o


def _usb():
    o = blob()
    o += path("M60,96 L104,52 L142,90 L98,134 Z", fill=NAVY)
    o += path("M104,52 L122,34 L160,72 L142,90 Z", fill=LAV)
    o += rect(128, 52, 8, 8, NAVY) + rect(140, 64, 8, 8, NAVY)
    o += circle(90, 104, 6, GREEN)
    o += circle(52, 50, 18, SUN) + rect(49, 40, 6, 13, NAVY, rx=3) + circle(52, 59, 3.2, NAVY)
    o += sparkle(170, 118, 7, GREEN)
    return o


def _password():
    o = blob()
    o += rect(28, 46, 120, 62, WHITE, rx=12) + rect(28, 46, 120, 62, "none", rx=12, stroke=NAVY, sw=4)
    for i in range(4):
        o += circle(56 + i * 22, 77, 7, NAVY)
    o += circle(150, 112, 18, SUN) + circle(150, 112, 7, WHITE)
    o += path("M136,124 L110,150 M118,142 L126,150 M112,148 L118,154", stroke=SUN, sw=7)
    o += rect(40, 116, 50, 8, GREEN, rx=4)
    o += sparkle(176, 40, 7, GREEN) + sparkle(30, 30, 5, SUN)
    return o


def _phishing():
    o = blob()
    o += path("M120,14 L120,52 C120,70 96,70 96,54", stroke=NAVY, sw=5)
    o += poly([(96, 54), (90, 64), (102, 62)], NAVY)
    o += rect(36, 70, 120, 72, WHITE, rx=8)
    o += path("M36,76 L96,112 L156,76", stroke=NAVY, sw=5)
    o += rect(48, 120, 40, 6, MINT, rx=3)
    o += circle(158, 74, 15, SUN) + rect(155, 64, 6, 12, NAVY, rx=3) + circle(158, 82, 3, NAVY)
    o += sparkle(36, 40, 6, GREEN)
    return o


def _smishing():
    o = blob()
    o += rect(62, 14, 76, 136, NAVY, rx=14) + rect(70, 28, 60, 104, WHITE, rx=4)
    o += rect(76, 38, 40, 18, MINT_BG, rx=6) + rect(84, 62, 40, 18, GREEN, rx=6)
    o += rect(76, 86, 44, 18, MINT_BG, rx=6) + rect(80, 94, 30, 3, TEAL, rx=1.5)
    o += rect(92, 138, 16, 4, WHITE, rx=2, op=0.6)
    o += path("M144,46 C162,46 172,58 172,72", stroke=SUN, sw=5) + arrow_head(172, 82, 0, 10, 10, SUN)
    o += circle(40, 112, 16, SUN) + rect(37, 102, 6, 12, NAVY, rx=3) + circle(40, 120, 3, NAVY)
    return o


def _ransomware():
    o = blob()
    o += path("M30,52 H78 L88,64 H160 V136 H30 Z", fill=TEAL)
    o += rect(30, 70, 130, 66, GREEN, rx=4)
    o += path("M83,98 L83,88 A12,12 0 0 1 107,88 L107,98", stroke=WHITE, sw=6)
    o += rect(76, 96, 38, 30, WHITE, rx=5) + circle(95, 108, 4, NAVY) + rect(93, 110, 4, 8, NAVY, rx=1)
    o += circle(160, 44, 16, SUN) + circle(160, 44, 9, WHITE, op=0.6)
    o += circle(138, 28, 11, SUN) + sparkle(36, 34, 6, NAVY)
    return o


def _hacking():
    o = blob()
    o += rect(30, 28, 120, 82, NAVY, rx=8) + rect(38, 36, 104, 66, TEAL, rx=4)
    o += path("M20,110 H160 L152,122 H28 Z", fill=NAVY)
    o += circle(90, 70, 15, SUN) + circle(90, 52, 8, SUN)
    for dx in (-1, 1):
        o += path(f"M{90 + dx * 14},{62} L{90 + dx * 26},{56} M{90 + dx * 15},{72} L{90 + dx * 28},{72} "
                  f"M{90 + dx * 13},{80} L{90 + dx * 24},{88}", stroke=SUN, sw=3)
    o += path("M90,58 L90,84", stroke=NAVY, sw=2.5)
    o += rect(150, 62, 32, 70, GREEN, rx=8) + rect(155, 70, 22, 46, WHITE, rx=2)
    o += sparkle(176, 36, 6, SUN)
    return o


def _deepface():
    o = blob()
    for x, y, dx, dy in [(40, 24, 1, 1), (160, 24, -1, 1), (40, 140, 1, -1), (160, 140, -1, -1)]:
        o += path(f"M{x},{y + dy * 22} L{x},{y} L{x + dx * 22},{y}", stroke=GREEN, sw=5)
    o += person(100, 66, 20, NAVY, "short", bottom=136, collar=False)
    o += path("M48,92 H152", stroke=SUN, sw=4)
    o += sparkle(178, 80, 6, TEAL)
    return o


def _ai():
    o = blob()
    o += path("M100,28 L100,14", stroke=NAVY, sw=4) + circle(100, 12, 6, SUN)
    o += rect(56, 28, 88, 66, NAVY, rx=20) + rect(66, 40, 68, 42, MINT_BG, rx=14)
    o += circle(86, 61, 7, NAVY) + circle(114, 61, 7, NAVY) + rect(90, 72, 20, 4, TEAL, rx=2)
    o += rect(48, 52, 8, 20, TEAL, rx=3) + rect(144, 52, 8, 20, TEAL, rx=3)
    o += rect(70, 98, 60, 44, GREEN, rx=14) + circle(100, 120, 8, WHITE)
    o += rect(140, 102, 46, 30, WHITE, rx=10) + poly([(146, 128), (142, 142), (156, 130)], WHITE)
    o += rect(148, 112, 28, 4, MINT, rx=2) + rect(148, 120, 18, 4, MINT, rx=2)
    o += sparkle(30, 40, 7, SUN)
    return o


def _siren():
    o = blob()
    o += path("M64,112 L64,76 A36,36 0 0 1 136,76 L136,112 Z", fill=SUN)
    o += path("M80,104 L80,78 A20,20 0 0 1 100,58", stroke=WHITE, sw=6, op=None)
    o += rect(52, 110, 96, 20, NAVY, rx=6) + rect(44, 128, 112, 12, TEAL, rx=4)
    for x1, y1, x2, y2 in [(100, 22, 100, 8), (54, 40, 44, 30), (146, 40, 156, 30), (34, 76, 20, 76), (166, 76, 180, 76)]:
        o += path(f"M{x1},{y1} L{x2},{y2}", stroke=GREEN, sw=5)
    return o


def _lockscreen():
    o = blob()
    o += rect(34, 26, 132, 88, NAVY, rx=10) + rect(42, 34, 116, 72, TEAL, rx=5)
    o += path("M88,70 L88,60 A12,12 0 0 1 112,60 L112,70", stroke=WHITE, sw=5)
    o += rect(82, 68, 36, 28, WHITE, rx=5) + circle(100, 80, 4, TEAL) + rect(98, 82, 4, 7, TEAL, rx=1)
    o += rect(90, 114, 20, 16, NAVY) + rect(66, 128, 68, 8, NAVY, rx=4)
    o += plant(176, 136, 0.8)
    o += sparkle(26, 36, 6, SUN)
    return o


def _confidential():
    o = blob()
    o += rect(58, 30, 84, 108, WHITE, rx=8) + rect(46, 20, 84, 108, WHITE, rx=8)
    o += rect(46, 20, 84, 22, NAVY, rx=8) + rect(46, 32, 84, 10, NAVY)
    for i, w in enumerate([56, 40, 60, 46]):
        o += rect(58, 54 + i * 14, w, 5, MINT if i % 2 else LAV, rx=2)
    o += circle(140, 104, 24, GREEN)
    o += path("M126,104 C134,94 146,94 154,104 C146,114 134,114 126,104 Z", fill=WHITE)
    o += circle(140, 104, 5, GREEN) + path("M126,118 L154,90", stroke=WHITE, sw=4)
    o += sparkle(170, 36, 6, SUN)
    return o


def wheelchair_user(cx, base, s=1.0, shirt=TEAL, hair="short"):
    """Seated person in a wheelchair, facing right; cx = chair centre, base = floor y."""
    k = s
    o = ""
    wy = base - 30 * k
    o += circle(cx - 6 * k, wy, 30 * k, "none", stroke=NAVY, sw=6 * k)                 # big wheel
    o += circle(cx - 6 * k, wy, 5 * k, NAVY)
    o += circle(cx + 34 * k, base - 8 * k, 8 * k, "none", stroke=NAVY, sw=4 * k)        # caster
    o += path(f"M{r1(cx - 30 * k)},{r1(wy - 44 * k)} L{r1(cx - 22 * k)},{r1(wy - 4 * k)} L{r1(cx + 30 * k)},{r1(wy - 4 * k)} "
              f"L{r1(cx + 34 * k)},{r1(base - 16 * k)}", stroke=NAVY, sw=4 * k)            # frame
    o += path(f"M{r1(cx - 36 * k)},{r1(wy - 48 * k)} L{r1(cx - 26 * k)},{r1(wy - 46 * k)}", stroke=NAVY, sw=5 * k)  # handle
    # body: torso, thighs, shins
    o += path(f"M{r1(cx - 22 * k)},{r1(wy - 8 * k)} L{r1(cx - 24 * k)},{r1(wy - 50 * k)} "
              f"Q{r1(cx - 22 * k)},{r1(wy - 62 * k)} {r1(cx - 8 * k)},{r1(wy - 62 * k)} "
              f"Q{r1(cx + 4 * k)},{r1(wy - 62 * k)} {r1(cx + 4 * k)},{r1(wy - 48 * k)} L{r1(cx + 2 * k)},{r1(wy - 8 * k)} Z",
              fill=shirt)
    o += path(f"M{r1(cx - 16 * k)},{r1(wy - 12 * k)} L{r1(cx + 26 * k)},{r1(wy - 12 * k)} L{r1(cx + 28 * k)},{r1(base - 14 * k)}",
              stroke=NAVY, sw=12 * k, cap="round")
    o += path(f"M{r1(cx - 4 * k)},{r1(wy - 44 * k)} L{r1(cx + 14 * k)},{r1(wy - 26 * k)}", stroke=shirt, sw=9 * k)  # arm
    o += circle(cx + 15 * k, wy - 25 * k, 4.5 * k, SKIN)
    o += rect(cx - 12 * k, wy - 70 * k, 9 * k, 10 * k, SKIN_2)
    o += circle(cx - 8 * k, wy - 78 * k, 13 * k, SKIN)
    hr = 13.8 * k
    hx, hy = cx - 8 * k, wy - 78 * k
    o += path(f"M{r1(hx - hr)},{r1(hy)} A{r1(hr)},{r1(hr)} 0 0 1 {r1(hx + hr)},{r1(hy)} "
              f"Q{r1(hx + 2 * k)},{r1(hy - 9 * k)} {r1(hx - 6 * k)},{r1(hy - 3 * k)} Q{r1(hx - 10 * k)},{r1(hy)} {r1(hx - hr)},{r1(hy)} Z",
              fill=NAVY)
    if hair == "long":
        o += rect(hx - hr, hy - 2 * k, 7 * k, 22 * k, NAVY, rx=3 * k)
    return o


def _wheelchair():
    o = blob()
    o += wheelchair_user(96, 146, 1.25, TEAL)
    o += sparkle(162, 40, 8, SUN) + sparkle(36, 52, 5, GREEN) + circle(168, 110, 4, MINT)
    return o


def _inclusion():
    """Colleagues together — two standing people and a wheelchair user."""
    o = blob()
    o += person(40, 66, 16, NAVY, "long", bottom=150)
    o += person(162, 62, 17, GREEN, "short", bottom=150)
    o += wheelchair_user(100, 152, 0.95, TEAL, "short")
    o += sparkle(178, 34, 7, SUN) + sparkle(24, 40, 5, TEAL)
    o += path("M86,28 C86,20 96,20 96,28 C96,20 106,20 106,28 C106,36 96,40 96,44 C96,40 86,36 86,28 Z", fill=GREEN)
    return o


LIB = {
    # key: (drawing, 한국어 의미, keywords for auto-pick)
    "thinking": (_thinking, "고민·질문하는 사람", "질문 궁금 고민 생각 왜 무엇 정의 의문 퀴즈 물음"),
    "presenter": (_presenter, "강의·설명하는 사람", "강의 설명 발표 소개 교육 수업 오리엔테이션 개요"),
    "idea": (_idea, "아이디어 전구", "아이디어 핵심 인사이트 팁 원리 깨달음 포인트 창의"),
    "team": (_team, "팀·구성원 세 사람", "팀 조직 구성원 직원 동료 협업 관계 사람 고객 리더"),
    "growth": (_growth, "성장 막대그래프", "성장 성과 증가 매출 지표 데이터 결과 생산성 통계"),
    "target": (_target, "목표 과녁", "목표 지향 방향 전략 목적 집중 KPI"),
    "security": (_security, "보안 방패·자물쇠", "보안 개인정보 보호 안전 정보보호 암호 유출 법 규정"),
    "checklist": (_checklist, "체크리스트 클립보드", "체크 점검 확인 절차 준수 실행 항목 요약 정리"),
    "chat": (_chat, "대화 말풍선", "소통 대화 커뮤니케이션 질의 응답 피드백 상담 Q&A"),
    "laptop": (_laptop, "노트북 업무", "업무 시스템 디지털 온라인 도구 IT 실습 화면"),
    "steps": (_steps, "계단을 오르는 단계", "단계 프로세스 절차 로드맵 성장 레벨 순서"),
    "search": (_search, "돋보기 문서 검토", "분석 검토 조사 사례 찾기 확인 진단 문서"),
    "book": (_book, "펼친 책 학습", "학습 지식 개념 이론 정의 배움 독서 강의순서 목차"),
    "calendar": (_calendar, "달력과 시계", "일정 기간 시간 계획 마감 보존 기한 스케줄"),
    "trophy": (_trophy, "트로피 성취", "성취 우수 성공 보상 동기부여 인정 마무리 결론"),
    "puzzle": (_puzzle, "맞물린 퍼즐", "협력 연결 통합 구성요소 시너지 조화 해결"),
    "alert": (_alert, "주의 경고 삼각형", "주의 경고 위반 위험 금지 사고 처벌 리스크 유의"),
    "idcard": (_idcard, "신분증·개인 정보 카드", "개인정보 신원 식별 주민번호 이름 회원 정보주체 유족"),
    "video": (_video, "영상 재생 화면", "영상 동영상 콘텐츠 이러닝 미디어 시청"),
    "goal": (_goal, "정상의 깃발", "도전 비전 미래 목표달성 정상 동기 성공"),
    "printer": (_printer, "프린터 출력물", "출력 프린터 인쇄 출력물 회수 복합기"),
    "shredder": (_shredder, "문서 파쇄기", "파쇄 파기 분쇄 폐기 문서처리"),
    "usb": (_usb, "USB 외부 저장장치", "USB 외장하드 저장장치 이동식 복사 분실"),
    "password": (_password, "비밀번호·열쇠", "비밀번호 인증 계정 접근 권한 로그인 2단계"),
    "phishing": (_phishing, "피싱 메일", "피싱 이메일 메일 낚시 사칭 스팸"),
    "smishing": (_smishing, "스미싱 문자", "스미싱 문자 SMS 메시지 링크 휴대폰"),
    "ransomware": (_ransomware, "랜섬웨어 잠긴 파일", "랜섬웨어 암호화 감염 몸값 파일잠금"),
    "hacking": (_hacking, "해킹·악성코드", "해킹 악성코드 바이러스 메모리 웜 침입"),
    "deepface": (_deepface, "얼굴 합성·딥페이크", "딥페이크 합성 얼굴 음성 사칭 위조 영상"),
    "ai": (_ai, "생성형 AI 챗봇", "AI 인공지능 생성형 챗봇 학습 프롬프트"),
    "siren": (_siren, "신고 경광등", "신고 긴급 사고 대응 경보 118"),
    "lockscreen": (_lockscreen, "화면 잠금", "화면잠금 부재 자리 잠금 보안유지 PC"),
    "confidential": (_confidential, "기밀 문서 노출 금지", "기밀 노출 문서 고객정보 민감정보 보관"),
    "wheelchair": (_wheelchair, "휠체어 사용자", "휠체어 장애인 지체장애 이동 접근성 편의"),
    "inclusion": (_inclusion, "함께하는 동료·가족 (휠체어 사용자 포함)", "함께 동료 가족 이웃 공존 인식개선 다양성 포용"),
}


def names():
    return list(LIB)


def pick(text_):
    """Choose an illustration by keyword overlap with the slide text (fallback: 'idea')."""
    best, score = "idea", 0
    for k, (_, _, kw) in LIB.items():
        s = sum(1 for w in kw.split() if w and w in text_)
        if s > score:
            best, score = k, s
    return best


def place(name, x, y, w, h, backdrop=True):
    """Place drawing `name` inside the box (x, y, w, h), aspect preserved, centred."""
    if name not in LIB:
        warn(f"unknown illustration '{name}' — available: {', '.join(LIB)}")
        name = "idea"
    s = min(w / BW, h / BH)
    ox, oy = x + (w - BW * s) / 2, y + (h - BH * s) / 2
    body = LIB[name][0]()
    if not backdrop:
        body = body.replace(blob(), "", 1)
    return f'  <g transform="translate({r1(ox)},{r1(oy)}) scale({round(s, 4)})">\n{body}  </g>\n'
