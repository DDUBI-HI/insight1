"""evkit.illust — spot illustration library for edu-video decks.

Flat line-art in the Insightlearning palette: navy 3px outlines, white fills, one soft
tint blob behind, small sparkles/dots. Every shape is drawn at ABSOLUTE coordinates
(no group scale) because svg_to_pptx does not scale stroke-width with a group transform —
this keeps the stroke weight identical in SVG and in the native PPTX, and every shape stays
editable in PowerPoint.

Each illustration is authored in a 240×240 local box and placed with
    draw(name, x, y, size, dark=False) -> svg fragment
`dark=True` swaps to the navy-shell variant (white lines, navy fills, sky sparkles).

Authoring rule for new illustrations: absolute path commands only (M L H V C Q Z) — no arcs
(`A`) and no lowercase relative commands, so the scaler can map every number.
"""
import math
import re

NAVY, SOFT, INK, SKY, MUTE, WHITE = "#012281", "#E0EDF3", "#1F375D", "#58CCFF", "#C2C2C2", "#FFFFFF"

_TOK = re.compile(r"[A-Za-z]|-?\d*\.?\d+(?:e-?\d+)?")


class Pen:
    def __init__(self, x, y, size, dark=False):
        self.ox, self.oy, self.s = x, y, size / 240.0
        self.dark = dark
        self.LINE = WHITE if dark else NAVY
        self.FILL = NAVY if dark else WHITE
        self.BLOB = INK if dark else SOFT
        self.ACC = SKY if dark else NAVY
        self.MUTE = "#D2D6E3" if dark else MUTE
        self.sw = 3 if size >= 160 else 2.5
        self.o = []

    # coordinate mapping
    def X(self, v):
        return round(self.ox + v * self.s, 1)

    def Y(self, v):
        return round(self.oy + v * self.s, 1)

    def L(self, v):
        return round(v * self.s, 1)

    def d(self, path):
        out, cmd, axis = [], None, 0
        for tok in _TOK.findall(path):
            if tok.isalpha():
                if tok not in "MLHVCQZ":
                    raise ValueError(f"illust path command {tok!r} not allowed (use absolute M L H V C Q Z)")
                cmd, axis = tok, 0
                out.append(tok)
                continue
            v = float(tok)
            if cmd == "H":
                out.append(str(self.X(v)))
            elif cmd == "V":
                out.append(str(self.Y(v)))
            else:
                out.append(str(self.X(v) if axis % 2 == 0 else self.Y(v)))
                axis += 1
        return " ".join(out)

    def _stroke(self, stroke, sw, dash=None):
        if not stroke:
            return ' stroke="none"'
        c = self.LINE if stroke is True else stroke
        da = f' stroke-dasharray="{dash}"' if dash else ''
        return (f' stroke="{c}" stroke-width="{sw or self.sw}" stroke-linecap="round" '
                f'stroke-linejoin="round"{da}')

    # primitives (fill None → no fill)
    def path(self, d, fill=None, stroke=True, sw=None, dash=None):
        f = fill or "none"
        self.o.append(f'  <path d="{self.d(d)}" fill="{f}"{self._stroke(stroke, sw, dash)}/>\n')

    def circle(self, cx, cy, r, fill=None, stroke=True, sw=None):
        f = fill or "none"
        self.o.append(f'  <circle cx="{self.X(cx)}" cy="{self.Y(cy)}" r="{self.L(r)}" fill="{f}"{self._stroke(stroke, sw)}/>\n')

    def rect(self, x, y, w, h, rx=0, fill=None, stroke=True, sw=None):
        f = fill or "none"
        a = f' rx="{self.L(rx)}"' if rx else ''
        self.o.append(f'  <rect x="{self.X(x)}" y="{self.Y(y)}" width="{self.L(w)}" height="{self.L(h)}"{a} '
                      f'fill="{f}"{self._stroke(stroke, sw)}/>\n')

    def line(self, x1, y1, x2, y2, c=None, sw=None):
        self.o.append(f'  <line x1="{self.X(x1)}" y1="{self.Y(y1)}" x2="{self.X(x2)}" y2="{self.Y(y2)}" '
                      f'stroke="{c or self.LINE}" stroke-width="{sw or self.sw}" stroke-linecap="round"/>\n')

    # motifs
    def blob(self):
        self.path("M120 18 C178 16 224 60 222 118 C220 178 176 224 116 222 C58 220 16 176 18 118 "
                  "C20 62 64 20 120 18 Z", fill=self.BLOB, stroke=False)

    def sparkle(self, cx, cy, r):
        k = r * 0.22
        self.path(f"M{cx} {cy - r} Q{cx + k} {cy - k} {cx + r} {cy} Q{cx + k} {cy + k} {cx} {cy + r} "
                  f"Q{cx - k} {cy + k} {cx - r} {cy} Q{cx - k} {cy - k} {cx} {cy - r} Z", fill=self.ACC, stroke=False)

    def dot(self, cx, cy, r=5, fill=None):
        self.circle(cx, cy, r, fill=fill or self.ACC, stroke=False)

    def ring(self, cx, cy, r=6):
        self.circle(cx, cy, r, fill=None, stroke=self.ACC, sw=2.5)

    def svg(self):
        return "".join(self.o)


# ───────────────────────────── illustrations ─────────────────────────────

def _person(p, cx, top, r=36, body="fill", hair="short"):
    """Bust: head centre (cx, top+r), shoulders below. body ∈ fill | line."""
    hy = top + r
    by = hy + r + 10
    p.rect(cx - 10, hy + r - 12, 20, 24, fill=p.FILL)
    bf = p.FILL if body == "fill" else p.LINE
    bw = min(62, r * 1.8)
    p.path(f"M{cx - bw} 232 C{cx - bw} {by + 22} {cx - bw * 0.55} {by} {cx} {by} C{cx + bw * 0.55} {by} {cx + bw} {by + 22} "
           f"{cx + bw} 232 Z", fill=bf)
    if body == "fill":
        p.path(f"M{cx - 16} {by + 2} L{cx} {by + 22} L{cx + 16} {by + 2}")
    p.circle(cx, hy, r, fill=p.FILL)
    k = r / 36.0
    if hair == "short":
        p.path(f"M{cx - 36 * k} {hy - 2 * k} C{cx - 36 * k} {hy - 30 * k} {cx - 20 * k} {hy - 42 * k} {cx + 2 * k} {hy - 42 * k} "
               f"C{cx + 26 * k} {hy - 42 * k} {cx + 38 * k} {hy - 26 * k} {cx + 36 * k} {hy - 4 * k} "
               f"C{cx + 28 * k} {hy - 14 * k} {cx + 16 * k} {hy - 20 * k} {cx} {hy - 18 * k} "
               f"C{cx - 16 * k} {hy - 16 * k} {cx - 28 * k} {hy - 10 * k} {cx - 36 * k} {hy - 2 * k} Z", fill=p.LINE)
    else:  # bob
        p.path(f"M{cx - 38 * k} {hy + 22 * k} C{cx - 44 * k} {hy - 18 * k} {cx - 26 * k} {hy - 42 * k} {cx + 2 * k} {hy - 42 * k} "
               f"C{cx + 30 * k} {hy - 42 * k} {cx + 46 * k} {hy - 18 * k} {cx + 38 * k} {hy + 22 * k} "
               f"C{cx + 32 * k} {hy + 8 * k} {cx + 32 * k} {hy - 4 * k} {cx + 26 * k} {hy - 14 * k} "
               f"C{cx + 8 * k} {hy - 12 * k} {cx - 12 * k} {hy - 18 * k} {cx - 26 * k} {hy - 12 * k} "
               f"C{cx - 32 * k} {hy - 2 * k} {cx - 32 * k} {hy + 8 * k} {cx - 38 * k} {hy + 22 * k} Z", fill=p.LINE)
    p.dot(cx - 12 * k, hy + 6 * k, 3.5 * k, fill=p.LINE)
    p.dot(cx + 12 * k, hy + 6 * k, 3.5 * k, fill=p.LINE)
    p.path(f"M{cx - 9 * k} {hy + 18 * k} C{cx - 4 * k} {hy + 23 * k} {cx + 4 * k} {hy + 23 * k} {cx + 9 * k} {hy + 18 * k}")


def question(p):
    """Learner wondering — replaces the clip-art businessman."""
    p.blob()
    _person(p, 112, 80)
    p.circle(186, 56, 30, fill=p.FILL)
    p.path("M176 48 C176 34 197 34 197 48 C197 57 187 58 187 68", sw=4)
    p.dot(187, 78, 3.5, fill=p.LINE)
    p.circle(162, 94, 6, fill=p.FILL, sw=2.5)
    p.circle(150, 108, 3.5, fill=p.FILL, sw=2)
    p.sparkle(46, 62, 12)
    p.ring(40, 150)
    p.dot(208, 150, 4)


def idea(p):
    p.blob()
    p.path("M120 46 C86 46 62 72 62 104 C62 128 76 142 88 154 C96 162 98 170 98 178 L142 178 "
           "C142 170 144 162 152 154 C164 142 178 128 178 104 C178 72 154 46 120 46 Z", fill=p.FILL)
    p.rect(98, 178, 44, 16, 5, fill=p.FILL)
    p.rect(104, 194, 32, 14, 5, fill=p.LINE)
    p.path("M106 152 L106 126 C106 114 120 114 120 126 C120 114 134 114 134 126 L134 152")
    p.path("M84 100 C84 86 94 74 108 72")
    for x1, y1, x2, y2 in [(120, 16, 120, 30), (56, 40, 66, 50), (184, 40, 174, 50), (30, 102, 44, 102), (196, 102, 210, 102)]:
        p.line(x1, y1, x2, y2, c=p.ACC)
    p.sparkle(202, 164, 12)
    p.ring(40, 172)


def shield(p):
    p.blob()
    p.path("M120 30 L186 54 L186 110 C186 158 156 192 120 210 C84 192 54 158 54 110 L54 54 Z", fill=p.FILL)
    p.path("M120 50 L168 68 L168 110 C168 146 148 172 120 188 C92 172 72 146 72 110 L72 68 Z", fill=p.BLOB, stroke=False)
    p.path("M104 112 L104 98 C104 78 136 78 136 98 L136 112")
    p.rect(92, 110, 56, 44, 9, fill=p.FILL)
    p.dot(120, 127, 5.5, fill=p.LINE)
    p.line(120, 131, 120, 142, sw=4)
    p.sparkle(200, 40, 12)
    p.ring(36, 180)
    p.dot(210, 150, 4)


def id_card(p):
    p.blob()
    p.rect(34, 62, 172, 118, 14, fill=p.FILL)
    p.rect(34, 62, 172, 30, 14, fill=p.BLOB, stroke=False)
    p.rect(34, 78, 172, 14, fill=p.BLOB, stroke=False)
    p.rect(34, 62, 172, 118, 14)
    p.rect(50, 104, 54, 62, 8, fill=p.FILL)
    p.circle(77, 124, 10, fill=p.FILL, sw=2.5)
    p.path("M61 166 C61 146 93 146 93 166", fill=p.FILL, sw=2.5)
    p.line(118, 114, 186, 114, sw=5)
    p.line(118, 136, 176, 136, c=p.MUTE, sw=5)
    p.line(118, 156, 158, 156, c=p.MUTE, sw=5)
    p.circle(180, 178, 26, fill=p.FILL)
    p.circle(180, 178, 15, fill=p.BLOB, stroke=False)
    p.line(198, 196, 216, 214, sw=7)
    p.sparkle(208, 40, 11)
    p.ring(26, 204)


def document(p):
    p.blob()
    p.rect(76, 34, 112, 150, 10, fill=p.BLOB)
    p.path("M56 52 L144 52 L170 78 L170 206 L56 206 Z", fill=p.FILL)
    p.path("M144 52 L144 78 L170 78")
    p.line(76, 98, 130, 98, sw=5)
    p.line(76, 120, 150, 120, c=p.MUTE, sw=5)
    p.line(76, 142, 150, 142, c=p.MUTE, sw=5)
    p.line(76, 164, 116, 164, c=p.MUTE, sw=5)
    p.circle(172, 182, 26, fill=p.LINE, stroke=False)
    p.path("M160 182 L169 191 L185 174", stroke=p.FILL, sw=4)
    p.sparkle(36, 60, 11)
    p.dot(208, 58, 5)


def laptop(p):
    """Clean device mock — replaces the gray monitor screenshot frame."""
    p.blob()
    p.rect(46, 50, 148, 104, 10, fill=p.FILL)
    p.rect(58, 62, 124, 80, 4, fill=p.BLOB, stroke=False)
    p.rect(66, 70, 34, 64, 4, fill=p.FILL, stroke=False)
    p.line(74, 82, 92, 82, sw=4)
    p.line(74, 96, 88, 96, c=p.MUTE, sw=4)
    p.line(74, 110, 90, 110, c=p.MUTE, sw=4)
    p.line(110, 80, 172, 80, sw=4)
    p.rect(108, 92, 66, 42, 4, fill=p.FILL, stroke=False)
    for x, top in [(120, 112), (134, 104), (148, 116), (162, 100)]:
        p.line(x, 126, x, top, sw=5)
    p.path("M24 162 L216 162 L206 180 L34 180 Z", fill=p.FILL)
    p.line(104, 170, 136, 170, sw=3)
    p.path("M178 120 L178 150 L186 142 L192 154 L198 151 L192 139 L203 139 Z", fill=p.FILL, sw=2.5)
    p.sparkle(210, 48, 11)
    p.ring(28, 72)


def talk(p):
    """Two people in conversation — replaces stock group photos."""
    p.blob()
    _person(p, 78, 116, r=26)
    _person(p, 164, 122, r=26, body="line", hair="bob")
    p.rect(18, 36, 84, 52, 16, fill=p.FILL)
    p.path("M44 88 L40 104 L62 88", fill=p.FILL)
    p.line(46, 88, 60, 88, c=p.FILL, sw=4)
    for x in (44, 60, 76):
        p.dot(x, 62, 4.5, fill=p.LINE)
    p.rect(138, 28, 86, 52, 16, fill=p.LINE, stroke=False)
    p.path("M180 78 L190 94 L198 78 Z", fill=p.LINE, stroke=False)
    p.line(154, 48, 206, 48, c=p.FILL, sw=4)
    p.line(154, 62, 190, 62, c=p.FILL, sw=4)
    p.sparkle(120, 30, 9)


def checklist(p):
    p.blob()
    p.rect(62, 40, 116, 170, 12, fill=p.FILL)
    p.rect(94, 28, 52, 24, 8, fill=p.LINE, stroke=False)
    for i, y in enumerate((78, 118, 158)):
        p.rect(80, y, 24, 24, 6, fill=p.BLOB, sw=2.5)
        if i < 2:
            p.path(f"M85 {y + 12} L91 {y + 18} L100 {y + 7}", sw=3.5)
        p.line(116, y + 12, 160 if i != 1 else 150, y + 12, c=p.LINE if i == 0 else p.MUTE, sw=5)
    p.path("M178 176 L206 148 L220 162 L192 190 L174 194 Z", fill=p.FILL)
    p.line(200, 154, 214, 168, sw=2.5)
    p.sparkle(38, 62, 11)
    p.dot(212, 64, 5)


def target(p):
    p.blob()
    p.circle(110, 132, 78, fill=p.FILL)
    p.circle(110, 132, 54, fill=p.BLOB)
    p.circle(110, 132, 30, fill=p.FILL)
    p.circle(110, 132, 9, fill=p.LINE, stroke=False)
    p.line(114, 128, 190, 52, sw=4)
    p.path("M190 52 L206 52 L220 38 M190 52 L190 36 L204 22", sw=3)
    p.sparkle(36, 50, 11)
    p.ring(216, 176)


def growth(p):
    p.blob()
    p.path("M42 38 L42 198 L212 198")
    for x, top, f in [(62, 158, p.BLOB), (100, 132, p.BLOB), (138, 106, p.BLOB), (176, 74, p.LINE)]:
        p.rect(x, top, 26, 198 - top, 4, fill=f)
    p.path("M60 132 L100 108 L138 116 L184 60", sw=4)
    p.path("M168 58 L186 58 L186 76", sw=4)
    p.sparkle(212, 36, 11)
    p.dot(222, 124, 5)


def book(p):
    p.blob()
    p.path("M120 78 C100 64 70 60 40 64 L40 180 C70 176 100 180 120 194 Z", fill=p.FILL)
    p.path("M120 78 C140 64 170 60 200 64 L200 180 C170 176 140 180 120 194 Z", fill=p.FILL)
    for dy in (0, 22, 44):
        p.path(f"M58 {94 + dy} C76 {92 + dy} 92 {94 + dy} 104 {100 + dy}", stroke=p.MUTE, sw=3.5)
        p.path(f"M136 {100 + dy} C148 {94 + dy} 164 {92 + dy} 182 {94 + dy}", stroke=p.MUTE, sw=3.5)
    p.path("M166 62 L166 100 L176 92 L186 100 L186 61", fill=p.LINE, stroke=False)
    p.sparkle(120, 36, 13)
    p.dot(80, 34, 5)
    p.dot(160, 30, 4)
    p.ring(28, 206)


def warning(p):
    p.blob()
    p.path("M120 38 L208 194 L32 194 Z", fill=p.FILL, sw=4)
    p.path("M120 66 L184 180 L56 180 Z", fill=p.BLOB, stroke=False)
    p.line(120, 104, 120, 144, sw=9)
    p.dot(120, 164, 6, fill=p.LINE)
    p.line(40, 76, 54, 90, c=p.ACC)
    p.line(200, 76, 186, 90, c=p.ACC)
    p.ring(216, 140)


def _star(cx, cy, r):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((round(cx + rr * math.cos(a), 1), round(cy + rr * math.sin(a), 1)))
    return "M" + " L".join(f"{x} {y}" for x, y in pts) + " Z"


def trophy(p):
    p.blob()
    p.path("M78 62 L58 62 C50 62 48 70 48 78 C48 96 62 108 82 108")
    p.path("M162 62 L182 62 C190 62 192 70 192 78 C192 96 178 108 158 108")
    p.path("M78 46 L162 46 L162 92 C162 120 144 140 120 140 C96 140 78 120 78 92 Z", fill=p.FILL)
    p.path(_star(120, 90, 20), fill=p.ACC, stroke=False)
    p.rect(110, 140, 20, 26, fill=p.FILL)
    p.rect(82, 166, 76, 24, 7, fill=p.LINE, stroke=False)
    p.sparkle(48, 36, 11)
    p.sparkle(198, 152, 8)
    p.ring(36, 158)
    p.dot(206, 34, 4)


def mail(p):
    p.blob()
    p.rect(40, 70, 148, 104, 12, fill=p.FILL)
    p.path("M44 78 L114 128 L184 78")
    p.path("M44 168 L94 120 M184 168 L134 120", stroke=p.MUTE, sw=2.5)
    for y, x1 in ((98, 12), (120, 4), (142, 14)):
        p.line(x1, y, 26, y, c=p.ACC)
    p.circle(188, 72, 24, fill=p.LINE, stroke=False)
    p.line(188, 61, 188, 75, c=p.FILL, sw=4.5)
    p.dot(188, 84, 3.2, fill=p.FILL)
    p.ring(206, 190)
    p.sparkle(60, 40, 10)


def quiz(p):
    p.blob()
    p.rect(50, 46, 140, 152, 18, fill=p.FILL)
    p.path("M98 102 C98 76 142 76 142 102 C142 122 120 122 120 142", sw=10)
    p.dot(120, 166, 7, fill=p.LINE)
    p.circle(52, 192, 24, fill=p.LINE, stroke=False)
    p.circle(52, 192, 11, fill=None, stroke=p.FILL, sw=4)
    p.circle(192, 52, 24, fill=p.FILL)
    p.line(184, 44, 200, 60, sw=4)
    p.line(200, 44, 184, 60, sw=4)
    p.sparkle(208, 158, 11)


def graduate(p):
    p.blob()
    p.path("M64 120 L64 162 C64 178 92 192 120 192 C148 192 176 178 176 162 L176 120", fill=p.FILL)
    p.path("M120 54 L216 98 L120 142 L24 98 Z", fill=p.LINE)
    p.path("M120 98 L194 108 L194 160", sw=3)
    p.circle(194, 168, 7, fill=p.LINE, stroke=False)
    p.sparkle(40, 50, 12)
    p.sparkle(214, 40, 8)
    p.ring(30, 176)


def calendar(p):
    p.blob()
    p.rect(42, 56, 156, 142, 14, fill=p.FILL)
    p.rect(42, 56, 156, 36, 14, fill=p.LINE, stroke=False)
    p.rect(42, 76, 156, 16, fill=p.LINE, stroke=False)
    p.line(86, 42, 86, 66, sw=7)
    p.line(154, 42, 154, 66, sw=7)
    for r_, y in enumerate((108, 136, 164)):
        for c_, x in enumerate((60, 96, 132)):
            p.rect(x, y, 24, 18, 4, fill=p.LINE if (r_, c_) == (1, 1) else p.BLOB, stroke=False)
    p.circle(186, 180, 28, fill=p.FILL)
    p.path("M186 164 L186 180 L198 188")
    p.sparkle(214, 44, 10)
    p.dot(24, 120, 5)


def team(p):
    """Three colleagues — organisation culture, cover, '함께'."""
    p.blob()
    _person(p, 66, 112, r=24, body="line", hair="bob")
    _person(p, 174, 112, r=24, hair="short")
    _person(p, 120, 92, r=30, hair="short")
    p.sparkle(120, 22, 9)
    p.sparkle(36, 64, 10)
    p.ring(212, 70)


def phone(p):
    """Smartphone lighting up at night — after-hours messages."""
    p.blob()
    p.rect(72, 30, 96, 180, 18, fill=p.FILL)
    p.rect(84, 52, 72, 124, 6, fill=p.BLOB, stroke=False)
    p.line(108, 42, 132, 42, sw=3)
    p.circle(120, 192, 7, fill=p.FILL, sw=2.5)
    p.rect(92, 64, 56, 22, 8, fill=p.FILL, stroke=False)
    p.line(100, 75, 136, 75, sw=4)
    p.rect(92, 96, 44, 22, 8, fill=p.LINE, stroke=False)
    p.line(100, 107, 126, 107, c=p.FILL, sw=4)
    p.rect(100, 128, 48, 22, 8, fill=p.FILL, stroke=False)
    p.line(108, 139, 140, 139, sw=4)
    p.circle(166, 44, 18, fill=p.LINE, stroke=False)
    p.line(166, 36, 166, 46, c=p.FILL, sw=4)
    p.dot(166, 53, 2.6, fill=p.FILL)
    p.path("M44 58 C30 64 26 84 36 96 C42 102 52 104 60 100 C48 96 42 86 44 74 C45 68 46 62 44 58 Z", fill=p.ACC, stroke=False)
    p.sparkle(206, 112, 10)
    p.dot(200, 182, 5)
    p.ring(40, 164)


def scale(p):
    """Balance scale — law, fair judgement, investigation."""
    p.blob()
    p.line(120, 44, 120, 190, sw=4)
    p.circle(120, 40, 8, fill=p.LINE, stroke=False)
    p.line(56, 70, 184, 70, sw=4)
    p.path("M56 70 L36 128 M56 70 L76 128")
    p.path("M184 70 L164 128 M184 70 L204 128")
    p.path("M32 128 L80 128 C78 146 66 154 56 154 C46 154 34 146 32 128 Z", fill=p.FILL)
    p.path("M160 128 L208 128 C206 146 194 154 184 154 C174 154 162 146 160 128 Z", fill=p.FILL)
    p.rect(84, 190, 72, 18, 6, fill=p.LINE, stroke=False)
    p.sparkle(206, 38, 10)
    p.ring(30, 196)
    p.dot(214, 176, 4)


LIB = {
    "team": (team, "동료 세 사람 — 조직문화·표지·함께"),
    "phone": (phone, "밤의 스마트폰 알림 — 퇴근 후·휴가 중 연락"),
    "scale": (scale, "저울 — 법·공정한 판단·조사"),
    "question": (question, "궁금해하는 학습자 — 정의·개념 질문, 도입"),
    "idea": (idea, "전구 — 핵심 개념, 팁, 인사이트"),
    "shield": (shield, "방패+자물쇠 — 보안·보호·준수"),
    "id_card": (id_card, "신분증+돋보기 — 개인정보·식별·확인"),
    "document": (document, "문서+체크 — 규정·서류·승인"),
    "laptop": (laptop, "노트북 UI — 시스템·화면 안내 (모니터 캡처 대체)"),
    "talk": (talk, "대화하는 두 사람 — 사례·상담·커뮤니케이션 (스톡 사진 대체)"),
    "checklist": (checklist, "체크리스트 — 점검·절차·요약"),
    "target": (target, "과녁 — 목표·학습 목표"),
    "growth": (growth, "성장 차트 — 효과·추이·성과"),
    "book": (book, "펼친 책 — 학습·정의·이론"),
    "warning": (warning, "경고 삼각형 — 주의·위반·사고"),
    "trophy": (trophy, "트로피 — 완료·요약·마무리"),
    "mail": (mail, "봉투+알림 — 메일·발송·통지 사고"),
    "quiz": (quiz, "물음표 카드+OX — 퀴즈·확인 문제"),
    "graduate": (graduate, "학사모 — 표지·수료·엔딩"),
    "calendar": (calendar, "달력+시계 — 일정·기한·보관 기간"),
}


def draw(name, x, y, size=240, dark=False):
    if name not in LIB:
        raise KeyError(f"unknown illustration {name!r} — choose from: {', '.join(LIB)}")
    p = Pen(x, y, size, dark)
    LIB[name][0](p)
    return p.svg()
