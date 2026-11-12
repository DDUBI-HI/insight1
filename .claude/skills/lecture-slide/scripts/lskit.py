"""lskit — 강의 영상 배경 슬라이드 키트 (Lecture Video theme, 1280×720).

설계 원칙
  * 오른쪽 30 % (x ≥ 896)는 강사 영상 합성 영역 — 콘텐츠 금지. 배경(프레임·패널·띠)만 전체 폭.
  * 콘텐츠 존 x 56–856 (폭 800, 중심 CX=456). 헤더·푸터·본문 모두 이 안에 둔다.
  * 색은 PDF 원본에서 샘플링한 7색만 사용 (단일 액센트 #717FCB + 틴트).
  * 모든 primitive가 bounding box를 기록 → 페이지를 쓸 때 safe-zone 침범이면 SafeZoneError.

build.py가 deck.yaml을 읽어 이 모듈의 shell / layout 함수를 호출한다. 직접 써도 된다:
    import lskit as K
    K.OUT = "output/<project>/svg_output"
    K.content_page("02_statement.svg", "1-1. 개인정보 정의", "개인정보란?", gm, 2,
                   K.L_statement(K.TOP, K.BOTTOM, lines=[...], emphasis="..."))
"""
from __future__ import annotations

import math
import os
import textwrap
from pathlib import Path

# ─────────────────────────── tokens ───────────────────────────
W, H = 1280, 720
SAFE_X = 896                 # 70 % — 이 오른쪽은 강사 영역
L, R = 56, 856               # content zone
CX = (L + R) // 2            # 456
ZW = R - L                   # 800
TOP, TOP_LEAD, BOTTOM = 180, 214, 624

ACC = "#717FCB"     # primary periwinkle (frame, rules, eyebrow, numbers, filled shapes)
INK = "#22294A"     # titles · strong text · chevrons
BODY = "#636573"    # body / description text
BAND = "#E9E9F2"    # lavender band (top strip, footer band, side circles)
SOFT = "#F6F6FE"    # card / panel fill
MID = "#B6BDDF"     # mid tint (chapter footer, timeline step 2, grid lines)
PH = "#DBE1F3"      # image placeholder
WHITE = "#FFFFFF"
PALETTE = [ACC, INK, BODY, BAND, SOFT, MID, PH, WHITE]

F = "Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif"
ICON_DIR = Path(__file__).resolve().parents[4] / "assets" / "icons" / "tabler-outline"

OUT: str | None = None       # svg_output dir (build.py sets it)
WARN: list[str] = []         # collected layout warnings (printed by build.py)
_B: list[tuple] = []         # bounds of content primitives on the current page
_PAGE = "?"


class SafeZoneError(RuntimeError):
    pass


def warn(msg):
    WARN.append(f"[{_PAGE}] {msg}")


# ─────────────────────────── text metrics ───────────────────────────
def text_w(s: str, fs: float, fw: int = 400, ls: float = 0) -> float:
    """Pretendard 폭 (실측 0.864em에 2 % 여유): 한글 0.88em · 대문자 0.62 · 숫자 0.6 · 소문자 0.5 ·
    공백 0.26 · 문장부호 0.34. 굵은 라틴 +4 %."""
    w = lat = 0.0
    for c in s:
        if ord(c) >= 0x1100:
            w += fs * 0.88
        elif c == " ":
            w += fs * 0.26
        elif c in ".,:;'\"!|()[]·-_/":
            lat += fs * 0.34
        elif c.isupper() or c in "%#@&":
            lat += fs * 0.64
        elif c.isdigit():
            lat += fs * 0.6
        else:
            lat += fs * 0.5
    if fw >= 700:
        lat *= 1.04
    return w + lat + ls * max(len(s) - 1, 0)


def wrap(s: str, width: float, fs: float, fw: int = 400) -> list[str]:
    """폭(px) 기준 줄바꿈. '\n'은 강제 줄바꿈. 띄어쓰기 단위 우선, 긴 단어는 글자 단위."""
    out = []
    for para in str(s).split("\n"):
        line = ""
        for word in para.split(" "):
            cand = word if not line else line + " " + word
            if text_w(cand, fs, fw) <= width:
                line = cand
                continue
            if line:
                out.append(line)
            line = ""
            while text_w(word, fs, fw) > width:      # very long word → hard break
                k = len(word)
                while k > 1 and text_w(word[:k], fs, fw) > width:
                    k -= 1
                out.append(word[:k])
                word = word[k:]
            line = word
        out.append(line)
    return out


def fit(s: str, width: float, fs: float, fw: int = 400, min_fs: float = 0, ls: float = 0) -> float:
    """한 줄에 들어가도록 글자 크기를 줄인다 (min_fs까지)."""
    f = fs
    while text_w(s, f, fw, ls) > width and f > (min_fs or fs * 0.7):
        f -= 1
    return f


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ─────────────────────────── primitives (bounded) ───────────────────────────
def _reg(x0, y0, x1, y1, what):
    _B.append((x0, y0, x1, y1, what))


def t(x, y, s, fs=17, fw=400, fill=INK, anchor=None, ls=None, op=None):
    if s is None or s == "":
        return ""
    w = text_w(str(s), fs, fw, ls or 0)
    x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
    _reg(x0, y - fs * 0.85, x0 + w, y + fs * 0.25, f"text '{str(s)[:18]}'")
    a = f' text-anchor="{anchor}"' if anchor else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    o = f' fill-opacity="{op}"' if op is not None else ""
    return (f'  <text x="{x:.1f}" y="{y:.1f}" font-family="{F}" font-size="{fs}" font-weight="{fw}"'
            f'{l}{a} fill="{fill}"{o}>{esc(s)}</text>\n')


def tl(x, y, lines, fs=17, fw=400, fill=INK, anchor=None, lh=1.6, op=None):
    """여러 줄 텍스트. y = 첫 줄 baseline."""
    return "".join(t(x, y + i * fs * lh, s, fs, fw, fill, anchor, op=op) for i, s in enumerate(lines))


def r(x, y, w, h, fill=SOFT, rx=None, stroke=None, sw=1, dash=None, op=None):
    _reg(x, y, x + w, y + h, "rect")
    a = f' rx="{rx}"' if rx else ""
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' fill-opacity="{op}"' if op is not None else ""
    return f'  <rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"{a}{s}{d}{o}/>\n'


def circ(cx, cy, rad, fill=ACC, stroke=None, sw=1):
    ext = rad + (sw / 2 if stroke else 0)
    _reg(cx - ext, cy - ext, cx + ext, cy + ext, "circle")
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="{fill}"{s}/>\n'


def ln(x1, y1, x2, y2, c=ACC, w=1, dash=None):
    _reg(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), "line")
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'  <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w}"{d}/>\n'


def dash_h(x1, x2, y, c=ACC):
    return ln(x1, y, x2, y, c, 1.2, "5 4")


def dash_v(x, y1, y2, c=ACC):
    return ln(x, y1, x, y2, c, 1.2, "5 4")


def poly(pts, fill=ACC):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    _reg(min(xs), min(ys), max(xs), max(ys), "polygon")
    return f'  <polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{fill}"/>\n'


def ic(name, x, y, s=40, c=ACC):
    """Tabler outline 아이콘 (2px 라인아트). 없는 이름이면 경고 후 'point'."""
    if not (ICON_DIR / f"{name}.svg").exists():
        warn(f"icon '{name}' not found in tabler-outline — using 'point'")
        name = "point"
    _reg(x, y, x + s, y + s, f"icon {name}")
    return (f'  <use data-icon="tabler-outline/{name}" x="{x:.1f}" y="{y:.1f}" width="{s}" height="{s}" '
            f'fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>\n')


def icon_disc(cx, cy, rad, name, fill=ACC, c=WHITE):
    s = round(rad * 1.0)
    return circ(cx, cy, rad, fill) + ic(name, cx - s / 2, cy - s / 2, s, c)


def chev(cx, cy, d="right", s=30):
    """PDF의 굵은 잉크색 꺾쇠 (›, ⌄)."""
    return ic("chevron-" + d, cx - s / 2, cy - s / 2, s, INK)


def img(src, x, y, w, h):
    """src = images/ 안의 파일명. None/'' → 플레이스홀더(연한 블루 + 카메라). PPT에서 그림 바꾸기로 교체."""
    if not src:
        s = min(36, w / 4, h / 4)
        return r(x, y, w, h, PH) + ic("camera", x + w / 2 - s / 2, y + h / 2 - s / 2, s, ACC)
    _reg(x, y, x + w, y + h, f"image {src}")
    return (f'  <image href="../images/{esc(src)}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'preserveAspectRatio="xMidYMid slice"/>\n')


def pill(x, y, s, fs=18, fill=ACC, color=WHITE, h=None, padx=None, anchor="middle", fw=700, minw=0):
    """둥근 배지. anchor middle이면 x=중심, start면 x=왼쪽."""
    h = h or round(fs * 2.1)
    padx = padx if padx is not None else fs * 1.6
    w = max(text_w(s, fs, fw) + padx * 2, minw)
    x0 = x - w / 2 if anchor == "middle" else x
    return (r(x0, y, w, h, fill, rx=h / 2) +
            t(x0 + w / 2, y + h / 2 + fs * 0.36, s, fs, fw, color, "middle")), w


# ─────────────────────────── background (unbounded) ───────────────────────────
def _svg_open():
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n')


def _bg(kind="content"):
    """배경 레이어 — 전체 폭(강사 영역 포함). 프레임 20px + 흰 패널 + 띠."""
    if kind == "chapter":
        return (f'  <rect width="{W}" height="{H}" fill="{SOFT}"/>\n'
                f'  <rect x="20" y="20" width="1240" height="680" fill="{ACC}"/>\n'
                f'  <rect x="20" y="646" width="1240" height="54" fill="{MID}"/>\n')
    o = (f'  <rect width="{W}" height="{H}" fill="{ACC}"/>\n'
         f'  <rect x="20" y="20" width="1240" height="680" fill="{WHITE}"/>\n')
    if kind == "content":
        o += f'  <rect x="20" y="20" width="1240" height="22" fill="{BAND}"/>\n'
    else:  # cover / ending
        o += f'  <rect x="20" y="646" width="1240" height="54" fill="{BAND}"/>\n'
    return o


def _check_and_write(fname, parts):
    global _B
    bad = [b for b in _B if b[2] > SAFE_X - 0.5 or b[0] < 20 or b[3] > H]
    if bad:
        msg = "; ".join(f"{w} x={x0:.0f}–{x1:.0f}" for x0, _, x1, _, w in bad[:6])
        _B = []
        raise SafeZoneError(f"{fname}: content outside the left-70% zone (x ≤ {SAFE_X}) → {msg}")
    over = [b for b in _B if b[2] > R + 0.5]
    if over:
        warn("content passes the zone margin x=856 (still inside the 70% line): "
             + ", ".join(w for *_, w in over[:4]))
    _B = []
    if not OUT:
        raise RuntimeError("lskit.OUT is not set")
    Path(OUT).mkdir(parents=True, exist_ok=True)
    Path(OUT, fname).write_text("".join(parts) + "</svg>\n", encoding="utf-8")


def begin(fname):
    global _PAGE, _B
    _PAGE, _B = fname, []


# ─────────────────────────── shells ───────────────────────────
def _toplabels(left, right, color=INK, rule=ACC):
    o = ln(L, 58, R, 58, rule, 1.5)
    o += t(L + 8, 86, left, 13, 500, color, ls=0.4)
    o += t(R - 8, 86, right, 13, 500, color, "end", ls=0.4)
    return o


def _brand_band(brand, color=INK):
    return t(CX, 679, brand, 14, 600, color, "middle", ls=0.6) if brand else ""


def cover(fname, title, subtitle=None, badge=None, info=(), top_left="", top_right="", brand=""):
    """표지 (파일명에 'cover'). PDF p1: 상단 룰+라벨, 배지, 가는 부제, 굵은 제목, 정보 행."""
    o = [_svg_open(), _bg("cover"), _toplabels(top_left, top_right), _brand_band(brand)]
    fs = fit(title, ZW, 56, 800, 44, -1.2)
    lines = [title] if text_w(title, fs, 800, -1.2) <= ZW else wrap(title, ZW, fs, 800)[:2]
    block = (42 + 40 if badge else 0) + (34 + 30 if subtitle else 0) + len(lines) * fs * 1.2 + (90 if info else 0)
    y = 360 - block / 2
    if badge:
        s, _ = pill(CX, y, badge, 20, ACC, WHITE, h=44)
        o.append(s)
        y += 44 + 40
    if subtitle:
        o.append(t(CX, y + 30, subtitle, fit(subtitle, ZW, 34, 300, 26), 300, INK, "middle", ls=-0.5))
        y += 34 + 30
    for i, s in enumerate(lines):
        o.append(t(CX, y + fs * 0.95 + i * fs * 1.2, s, fs, 800, INK, "middle", ls=-1.2))
    y += len(lines) * fs * 1.2
    if info:
        o.append(_info_row(list(info), y + 70))
    _check_and_write(fname, o)


def _info_row(items, y, fs=16):
    gap = 36
    ws = [text_w(s, fs) for s in items]
    total = sum(ws) + gap * 2 * (len(items) - 1)
    if total > ZW:
        fs = 14
        ws = [text_w(s, fs) for s in items]
        total = sum(ws) + gap * 2 * (len(items) - 1)
    x = CX - total / 2
    o = ""
    for i, (s, w) in enumerate(zip(items, ws)):
        o += t(x, y, s, fs, 400, INK)
        x += w
        if i < len(items) - 1:
            o += ln(x + gap, y - 20, x + gap, y + 10, ACC, 1.5)
            x += gap * 2
    return o


def chapter(fname, title, label="CHAPTER 01", sub=None, top_left="", top_right="", brand=""):
    """간지 (파일명에 'chapter'). 페리윙클 전면 + 흰 배지 + 흰 대제목."""
    o = [_svg_open(), _bg("chapter"), _toplabels(top_left, top_right, WHITE, WHITE), _brand_band(brand)]
    s, _ = pill(CX, 250, label, 20, WHITE, ACC, h=44)
    o.append(s)
    fs = fit(title, ZW, 64, 800, 44, -1.5)
    lines = [title] if text_w(title, fs, 800, -1.5) <= ZW else wrap(title, ZW, fs, 800)[:2]
    for i, ln_ in enumerate(lines):
        o.append(t(CX, 370 + i * fs * 1.15, ln_, fs, 800, WHITE, "middle", ls=-1.5))
    if sub:
        o.append(t(CX, 370 + (len(lines) - 1) * fs * 1.15 + 62, sub, 20, 400, WHITE, "middle", op=0.85))
    _check_and_write(fname, o)


def ending(fname, line2, line1=None, badge="THANK YOU", contacts=(), top_left="", top_right="", brand=""):
    """엔딩 (파일명에 'ending'). PDF p23: 왼쪽 정렬 배지 + 가는 줄 + 굵은 줄, 연락처."""
    o = [_svg_open(), _bg("ending"), _toplabels(top_left, top_right), _brand_band(brand)]
    fs2 = fit(line2, ZW, 60, 800, 40, -1.4)
    y2 = 560
    if line1:
        o.append(t(L, y2 - 84, line1, fit(line1, ZW, 40, 300, 28), 300, INK, ls=-0.8))
    top = y2 - (84 if line1 else 0) - 40 - 72
    s, _ = pill(L, top, badge, 20, ACC, WHITE, h=44, anchor="start")
    o.append(s)
    o.append(t(L, y2, line2, fs2, 800, INK, ls=-1.4))
    if contacts:
        cw = max(text_w(c, 15) for c in contacts)
        if text_w(line2, fs2, 800) + cw + 48 <= ZW:      # PDF처럼 오른쪽 아래
            for i, c in enumerate(reversed(list(contacts))):
                o.append(t(R, y2 - i * 24, c, 15, 400, INK, "end"))
        else:                                            # 제목이 길면 아래 한 줄
            o.append(t(L, y2 + 44, "  ·  ".join(contacts), fit("  ·  ".join(contacts), ZW, 15, 400, 12), 400, INK))
    _check_and_write(fname, o)


def content_page(fname, eyebrow, title, gm, num, body, lead=None, brand=""):
    """콘텐츠 셸. PDF p2–22: 중앙 영문 eyebrow · 굵은 제목 · 페리윙클 룰 · 하단 룰 + GM + 쪽번호.
    모두 콘텐츠 존(x 56–856) 중심 CX=456에 정렬 — 오른쪽 30 %는 비운다."""
    if not gm:
        raise ValueError(f"{fname}: gm (governing message) is required on content pages")
    o = [_svg_open(), _bg("content")]
    o.append(t(CX, 82, eyebrow, 16, 500, ACC, "middle", ls=1))
    fs = fit(title, ZW, 36, 800, 28, -0.8)
    if text_w(title, fs, 800, -0.8) > ZW:
        warn(f"title too long even at {fs}px — shorten: '{title}'")
    o.append(t(CX, 128, title, fs, 800, INK, "middle", ls=-0.8))
    o.append(ln(L, 154, R, 154, ACC, 1.5))
    if lead:
        lfs = fit(lead, ZW, 18, 400, 15)
        o.append(t(CX, 190, lead, lfs, 400, INK, "middle"))
    o.append(body)
    o.append(ln(L, 644, R, 644, ACC, 1))
    bw = text_w(brand, 13, 500) if brand else 0
    gfs = 15
    room = 2 * min(CX - (L + bw + 24), (R - 40) - CX)
    while text_w(gm, gfs, 600) > room and gfs > 12:
        gfs -= 0.5
    if text_w(gm, gfs, 600) > room:
        warn(f"GM too long for the footer — shorten (≤ ~{int(room / 15)}자): '{gm}'")
    o.append(t(L, 674, brand, 13, 500, ACC, ls=0.4))
    o.append(t(CX, 674, gm, gfs, 600, INK, "middle"))
    o.append(t(R, 674, f"{num:02d}", 13, 500, ACC, "end"))
    _check_and_write(fname, o)


# ─────────────────────────── layouts (body fragments) ───────────────────────────
# 시그니처: L_xxx(top, bottom, **fields) -> svg 문자열. 영역 x L..R, y top..bottom.

def _item(it, *keys):
    """str | dict | list → 튜플 (keys 순서)."""
    if isinstance(it, dict):
        return tuple(it.get(k) for k in keys)
    if isinstance(it, (list, tuple)):
        return tuple(list(it) + [None] * (len(keys) - len(it)))[:len(keys)]
    return (it,) + (None,) * (len(keys) - 1)


def L_statement(top, bottom, lines=(), emphasis=None, note=None, icon=None, align="center"):
    """핵심 문장 강조 (첨부 화면 스타일): 일반 문장 2–3줄 + 액센트 강조 문장(밑줄)."""
    x, anc = (CX, "middle") if align == "center" else (L + 24, None)
    width = ZW - 48
    body = [s for ln_ in lines for s in wrap(ln_, width, 30)]
    efs = fit(emphasis or "", width, 42, 800, 30) if emphasis else 0
    em = wrap(emphasis, width, efs, 800)[:2] if emphasis else []
    h = (112 if icon else 0) + len(body) * 46 + (len(em) * efs * 1.25 + 22 if em else 0) + (52 if note else 0)
    y = top + max((bottom - top - h) / 2, 0)
    o = ""
    if icon:
        o += icon_disc(x if anc else L + 24 + 44, y + 44, 44, icon)
        y += 112
    for s in body:
        o += t(x, y + 32, s, 30, 400, INK, anc, ls=-0.4)
        y += 46
    if em:
        y += 14
        for s in em:
            o += t(x, y + efs, s, efs, 800, ACC, anc, ls=-0.8)
            w = text_w(s, efs, 800, -0.8)
            x0 = x - w / 2 if anc else x
            o += ln(x0, y + efs + 12, x0 + w, y + efs + 12, ACC, 3)
            y += efs * 1.25
        y += 8
    if note:
        o += t(x, y + 40, note, fit(note, width, 17, 400, 14), 400, BODY, anc)
    return o


def L_bullets(top, bottom, items=(), heading=None, numbered=True):
    """번호 목록 (PDF p14 오른쪽): 소프트 패널 + '01' 액센트 번호. item = str | {title, desc}."""
    its = [_item(i, "title", "desc") for i in items]
    n = max(len(its), 1)
    o = r(L, top, ZW, bottom - top, SOFT, rx=20)
    y = top + 28
    if heading:
        o += t(CX, y + 22, heading, 22, 700, ACC, "middle")
        o += dash_h(CX - 260, CX + 260, y + 46)
        y += 74
    tx, tw = L + 120, ZW - 168
    rows = []
    for ti, de in its:
        tlines = wrap(ti, tw, 20, 600 if de else 400)[:2]
        dlines = wrap(de, tw, 16)[:2] if de else []
        rows.append((tlines, dlines, len(tlines) * 30 + len(dlines) * 25))
    need = sum(rh for *_, rh in rows)
    gap = min(max((bottom - 24 - y - need) / n, 16), 44)
    y += max((bottom - 24 - y - need - gap * n) / 2, 0) + gap / 2
    for k, (tlines, dlines, rh) in enumerate(rows):
        if numbered:
            o += t(L + 64, y + 22, f"{k + 1:02d}", 22, 500, ACC, "middle")
        else:
            o += circ(L + 64, y + 15, 5, ACC)
        o += tl(tx, y + 22, tlines, 20, 600 if dlines else 400, INK, lh=1.5)
        if dlines:
            o += tl(tx, y + 22 + len(tlines) * 30 + 2, dlines, 16, 400, BODY, lh=1.55)
        y += rh + gap
    if y > bottom + 4:
        warn(f"bullets overflow by {y - bottom:.0f}px — fewer/shorter items")
    return o


def L_text_image(top, bottom, text="", image=None, tags=(), heading=None):
    """이미지 + 태그 + 본문 (PDF p4)."""
    ih = min(bottom - top - 16, 300)
    iw = round(ih * 4 / 3)
    iy = top + (bottom - top - ih) / 2
    o = img(image, L, iy, iw, ih)
    x = L + iw + 40
    tw = R - x
    lines = wrap(text, tw, 17)
    labs = ["#" + str(tg).lstrip("#") for tg in tags]
    trows, row, rw = [], [], 0.0               # tag pills, wrapped into rows
    for lab in labs:
        w = text_w(lab, 15, 600) + 36
        if row and rw + w > tw:
            trows.append(row)
            row, rw = [], 0.0
        row.append(lab)
        rw += w + 10
    if row:
        trows.append(row)
    th = len(trows) * 44 + (10 if trows else 0) + (40 if heading else 0) + len(lines) * 29
    y = top + max((bottom - top - th) / 2, 0)
    for row in trows:
        tx = x
        for lab in row:
            s, w = pill(tx, y, lab, 15, SOFT, ACC, h=34, anchor="start", fw=600, padx=18)
            o += s
            tx += w + 10
        y += 44
    if trows:
        y += 10
    if heading:
        o += t(x, y + 22, heading, 22, 700, INK)
        y += 42
    o += tl(x, y + 20, lines, 17, 400, INK, lh=1.7)
    if y + len(lines) * 29 > bottom + 4:
        warn("text_image body overflows — shorten the paragraph")
    return o


def L_two_col(top, bottom, cols=()):
    """2열 비교 (PDF p5): 키워드 제목 + 이미지 + 설명, 가운데 점선."""
    cs = [_item(c, "title", "image", "text") for c in cols][:2]
    cw = 360
    xs = [L + 8, R - 8 - cw]
    o = dash_v(CX, top + 60, bottom - 40)
    for x, (ti, im, tx) in zip(xs, cs):
        o += t(x + cw / 2, top + 28, ti, fit(ti or "", cw, 24, 700, 18), 700, INK, "middle")
        ih = min(230, bottom - top - 150)
        o += img(im, x, top + 52, cw, ih)
        o += tl(x + cw / 2, top + 52 + ih + 36, wrap(tx or "", cw, 16)[:3], 16, 400, BODY, "middle", lh=1.55)
    return o


def L_stats(top, bottom, items=()):
    """수치 강조 (PDF p6 / p7). item = {label, value, unit, icon?, desc?}.
    desc가 있으면 카드형(p7), 없으면 아이콘 원 + 점선 구분 패널형(p6)."""
    its = [_item(i, "label", "value", "unit", "icon", "desc") for i in items][:3]
    n = len(its) or 1
    o = ""
    if any(i[4] for i in its):                     # p7 cards
        gap = 24
        cw = (ZW - gap * (n - 1)) / n
        vfs = 84 if n <= 2 else 64
        for k, (lb, v, u, icn, de) in enumerate(its):
            x = L + k * (cw + gap)
            ccx = x + cw / 2
            o += r(x, top, cw, bottom - top, SOFT, rx=24)
            o += t(ccx, top + 54, lb, 20, 700, ACC, "middle")
            vw, uw = text_w(str(v), vfs, 800), text_w(u or "", 26, 500)
            vx = ccx - (vw + 8 + uw) / 2
            o += t(vx, top + 54 + vfs + 28, str(v), vfs, 800, INK, ls=-1)
            if u:
                o += t(vx + vw + 8, top + 54 + vfs + 28, u, 26, 500, INK)
            o += dash_h(x + 40, x + cw - 40, top + 54 + vfs + 66)
            o += tl(ccx, top + 54 + vfs + 112, wrap(de or "", cw - 64, 16)[:3], 16, 400, BODY, "middle", lh=1.6)
        return o
    o += r(L, top, ZW, bottom - top, SOFT, rx=24)
    cw = ZW / n
    cy = top + (bottom - top) / 2
    for k, (lb, v, u, icn, _) in enumerate(its):
        ccx = L + cw * (k + 0.5)
        if k:
            o += dash_v(L + cw * k, cy - 120, cy + 120)
        o += t(ccx, cy - 106, lb, 19, 500, ACC, "middle")
        o += icon_disc(ccx, cy - 22, 46, icn or "chart-bar")
        vw, uw = text_w(str(v), 56, 800), text_w(u or "", 20, 500)
        vx = ccx - (vw + 6 + uw) / 2
        o += t(vx, cy + 100, str(v), 56, 800, INK, ls=-1)
        if u:
            o += t(vx + vw + 6, cy + 100, u, 20, 500, INK)
    return o


def L_cards(top, bottom, items=()):
    """아이콘 카드 3열 (PDF p10). 4개 이상이면 L_points(2×2)로 자동 전환."""
    its = [_item(i, "icon", "title", "desc") for i in items]
    if len(its) >= 4:
        return L_points(top, bottom, items)
    n = len(its) or 1
    gap = 20
    cw = (ZW - gap * (n - 1)) / n
    tls_all = [wrap(ti or "", cw - 48, 22, 700)[:2] for _, ti, _ in its]
    dls_all = [wrap(de or "", cw - 56, 16)[:5] for *_, de in its]
    need = 192 + max(len(x) for x in tls_all) * 30 + 40 + max(len(x) for x in dls_all) * 26 + 36
    ch = min(bottom - top, max(need, 300))
    y = top + (bottom - top - ch) / 2
    o = ""
    for k, (icn, ti, de) in enumerate(its):
        x = L + k * (cw + gap)
        ccx = x + cw / 2
        o += r(x, y, cw, ch, SOFT, rx=20)
        o += icon_disc(ccx, y + 92, 52, icn or "bulb")
        tls = tls_all[k]
        o += tl(ccx, y + 192, tls, 22, 700, INK, "middle", lh=1.35)
        yd = y + 192 + (max(len(x) for x in tls_all) - 1) * 30 + 30
        o += dash_h(ccx - 64, ccx + 64, yd)
        o += tl(ccx, yd + 40, dls_all[k], 16, 400, BODY, "middle", lh=1.6)
    return o


def L_points(top, bottom, items=()):
    """POINT 카드 2×2 (PDF p11): 왼쪽 아이콘 원 + POINT 0N + 제목 + 설명."""
    its = [_item(i, "icon", "title", "desc") for i in items][:4]
    rows = math.ceil(len(its) / 2) or 1
    gap = 16
    cw, ch = (ZW - gap) / 2, (bottom - top - gap * (rows - 1)) / rows
    o = ""
    for k, (icn, ti, de) in enumerate(its):
        x, y = L + (k % 2) * (cw + gap), top + (k // 2) * (ch + gap)
        o += r(x, y, cw, ch, SOFT, rx=16)
        cy = y + ch / 2
        o += icon_disc(x + 62, cy, 38, icn or "bulb")
        tx, tw = x + 122, cw - 122 - 20
        dl = wrap(de or "", tw, 16)[:3]
        bh = 26 + 32 + len(dl) * 24
        y0 = cy - bh / 2
        o += t(tx, y0 + 14, f"POINT {k + 1:02d}", 14, 600, ACC, ls=0.4)
        o += t(tx, y0 + 44, ti, fit(ti or "", tw, 20, 700, 16), 700, INK)
        o += tl(tx, y0 + 74, dl, 16, 400, BODY, lh=1.55)
    return o


def L_keywords(top, bottom, items=()):
    """키워드 3원 (PDF p13): 가운데 원 강조(액센트), 양옆 연보라."""
    its = [_item(i, "title", "desc") for i in items][:3]
    while len(its) < 3:
        its.append(("", ""))
    rad, off = 132, 250
    cy = top + (bottom - top) / 2
    o = circ(CX - off, cy, rad, BAND) + circ(CX + off, cy, rad, BAND) + circ(CX, cy, rad, ACC)
    for k, dx in ((0, -off), (2, off), (1, 0)):
        ti, de = its[k]
        hl = k == 1
        o += t(CX + dx, cy - 38, ti, fit(ti or "", 200, 26, 700, 18), 700, WHITE if hl else ACC, "middle")
        if not hl:
            o += dash_h(CX + dx - 56, CX + dx + 56, cy - 12)
        o += tl(CX + dx, cy + 26, wrap(de or "", 196, 16, 500 if hl else 400)[:3], 16, 500 if hl else 400, WHITE if hl else BODY, "middle", lh=1.55)
    return o


def L_chart(top, bottom, bars=(), heading=None, items=(), unit="", max_value=None):
    """막대 차트 + 해설 목록 (PDF p14). bars = [{label, value}] · items = 해설 문장."""
    bs = [_item(b, "label", "value") for b in bars]
    has_side = bool(items)
    cw = 400 if has_side else ZW
    o = r(L, top, cw, bottom - top, SOFT, rx=20)
    gx0, gx1, gy0, gy1 = L + 56, L + cw - 28, top + 44, bottom - 52
    vmax = max_value or (max([float(v) for _, v in bs] or [1]) * 1.0)
    step = 10 ** math.floor(math.log10(vmax)) if vmax > 0 else 1
    top_v = math.ceil(vmax / step) * step
    ticks = 5
    for i in range(ticks + 1):
        y = gy1 - (gy1 - gy0) * i / ticks
        o += ln(gx0, y, gx1, y, MID if i else BODY, 1)
        val = top_v * i / ticks
        o += t(gx0 - 10, y + 4, f"{val:g}", 12, 400, BODY, "end")
    n = len(bs) or 1
    slot = (gx1 - gx0) / n
    bw = min(slot * 0.46, 90)
    for k, (lb, v) in enumerate(bs):
        h = (gy1 - gy0) * float(v) / top_v
        bx = gx0 + slot * (k + 0.5) - bw / 2
        o += r(bx, gy1 - h, bw, h, ACC, rx=6)
        o += t(bx + bw / 2, gy1 - h - 8, f"{v:g}{unit}" if isinstance(v, (int, float)) else f"{v}{unit}", 13, 600, ACC, "middle")
        o += t(bx + bw / 2, gy1 + 24, lb, fit(lb, slot - 8, 13, 400, 10), 400, INK, "middle")
    if has_side:
        x = L + cw + 16
        w = R - x
        o += r(x, top, w, bottom - top, SOFT, rx=20)
        y = top + 52
        if heading:
            o += t(x + w / 2, y, heading, fit(heading, w - 40, 20, 700, 16), 700, ACC, "middle")
            o += dash_h(x + 32, x + w - 32, y + 26)
            y += 70
        for k, s in enumerate(items):
            ls_ = wrap(s, w - 92, 17)[:2]
            o += t(x + 32, y, f"{k + 1:02d}", 18, 500, ACC)
            o += tl(x + 68, y, ls_, 17, 400, INK, lh=1.5)
            y += len(ls_) * 25 + 26
    return o


def L_process(top, bottom, steps=(), result=None):
    """프로세스 (PDF p17): 소프트 캡슐 안의 원 N개 → 꺾쇠 → 결과 링."""
    ss = [_item(s, "title", "sub") for s in steps][:4]
    n = len(ss) or 1
    cy = top + (bottom - top) / 2
    rad = 56
    res = _item(result, "title", "sub") if result else None
    band_r = (R - 214) if res else R
    bx0 = L
    o = r(bx0, cy - 96, band_r - bx0, 192, SOFT, rx=96)
    step = (band_r - bx0 - 2 * 40 - 2 * rad) / max(n - 1, 1)
    for k, (ti, su) in enumerate(ss):
        ccx = bx0 + 40 + rad + step * k if n > 1 else (bx0 + band_r) / 2
        o += circ(ccx, cy, rad, ACC)
        o += t(ccx, cy - 2, ti, fit(ti or "", rad * 1.7, 19, 700, 13), 700, WHITE, "middle")
        if su:
            o += t(ccx, cy + 26, su, fit(su, rad * 1.7, 15, 500, 13), 500, WHITE, "middle")
    if res:
        o += chev(band_r + 24, cy)
        rcx = R - 82
        o += circ(rcx, cy, 72, WHITE, ACC, 16)
        o += t(rcx, cy - 2, res[0], fit(res[0] or "", 110, 19, 700, 13), 700, INK, "middle")
        if res[1]:
            o += t(rcx, cy + 26, res[1], fit(res[1], 110, 15, 500, 13), 500, INK, "middle")
    return o


def L_steps(top, bottom, items=()):
    """단계 (PDF p18): 연한 원 + 아이콘, 꺾쇠, STEP n + 액센트 제목."""
    its = [_item(i, "icon", "title", "label") for i in items][:4]
    n = len(its) or 1
    colw = ZW / n
    rad = min(70, colw / 2 - 30)
    cy = top + (bottom - top) / 2 - 50
    o = ""
    for k, (icn, ti, lb) in enumerate(its):
        ccx = L + colw * (k + 0.5)
        o += circ(ccx, cy, rad, SOFT) + ic(icn or "point", ccx - rad * 0.45, cy - rad * 0.45, round(rad * 0.9), ACC)
        if k < n - 1:
            o += chev(L + colw * (k + 1), cy, s=28)
        o += t(ccx, cy + rad + 44, lb or f"STEP {k + 1}", 16, 500, BODY, "middle", ls=0.3)
        for j, s in enumerate(wrap(ti or "", colw - 16, 22, 700)[:2]):
            o += t(ccx, cy + rad + 80 + j * 30, s, 22, 700, ACC, "middle")
    return o


def L_before_after(top, bottom, rows=(), quote=None, labels=None):
    """비교 전 → 후 (PDF p19): 왼쪽 액센트 박스(흰 글자) › 오른쪽 소프트 박스."""
    rs = [_item(x, "before", "after") for x in rows][:4]
    y = top
    o = ""
    if quote:
        o += t(CX, y + 22, quote, fit(quote, ZW, 18, 400, 14), 400, ACC, "middle")
        y += 48
    bw = 344
    if labels:
        o += t(L + bw / 2, y + 16, labels[0], 14, 700, ACC, "middle", ls=1)
        o += t(R - bw / 2, y + 16, labels[1], 14, 700, ACC, "middle", ls=1)
        y += 34
    n = len(rs) or 1
    gap = 18
    rh = min(84, (bottom - y - gap * (n - 1)) / n)
    y += max((bottom - y - n * rh - gap * (n - 1)) / 2, 0)
    for b, a in rs:
        o += r(L, y, bw, rh, ACC, rx=8)
        o += _cell_text(L + bw / 2, y + rh / 2, b, bw - 40, 17, 500, WHITE)
        o += chev(CX, y + rh / 2)
        o += r(R - bw, y, bw, rh, SOFT, rx=8)
        o += _cell_text(R - bw / 2, y + rh / 2, a, bw - 40, 17, 500, INK)
        y += rh + gap
    return o


def _cell_text(cx, cy, s, width, fs, fw, fill, anchor="middle", maxl=2):
    lines = wrap(s or "", width, fs, fw)[:maxl]
    lh = fs * 1.45
    y0 = cy - (len(lines) - 1) * lh / 2 + fs * 0.36
    return "".join(t(cx, y0 + i * lh, s_, fs, fw, fill, anchor) for i, s_ in enumerate(lines))


def L_cause_result(top, bottom, causes=(), result=""):
    """원인 → 결과 (PDF p20): 소프트 원인 박스 01/02 + 꺾쇠 + 액센트 결과 박스."""
    cs = list(causes)[:3]
    n = len(cs) or 1
    rh, gap = 76, 16
    total = n * rh + (n - 1) * gap + 66 + 84
    y = top + max((bottom - top - total) / 2, 0)
    o = ""
    for k, c in enumerate(cs):
        o += r(L, y, ZW, rh, SOFT, rx=10)
        lines = wrap(c, ZW - 140, 17)[:2]
        lw = max(text_w(s, 17) for s in lines)
        x0 = CX - (lw + 36) / 2
        o += t(x0, y + rh / 2 + 7 - (len(lines) - 1) * 12, f"{k + 1:02d}", 20, 500, ACC)
        o += tl(x0 + 36, y + rh / 2 + 6 - (len(lines) - 1) * 12, lines, 17, 400, BODY, lh=1.45)
        y += rh + gap
    y += -gap + 33
    o += chev(CX, y, "down")
    y += 33
    o += r(L, y, ZW, 84, ACC, rx=10)
    o += _cell_text(CX, y + 42, result, ZW - 80, 19, 700, WHITE)
    return o


def L_timeline(top, bottom, stages=()):
    """흐름 (PDF p21): 3–4단 셰브론 띠(소프트→미드→액센트) + 아래 아이콘·키워드·설명."""
    ss = [_item(s, "label", "icon", "title", "desc") for s in stages][:4]
    n = len(ss) or 1
    fills = [SOFT, MID, ACC] if n == 3 else ([SOFT, BAND, MID, ACC] if n == 4 else [SOFT, ACC][:n] if n <= 2 else [ACC] * n)
    bh, tip = 84, 36
    segw = (ZW - tip) / n
    y0 = top + 8
    o = ""
    for k in range(n - 1, -1, -1):               # draw right→left so tips overlap correctly
        x0 = L + k * segw
        x1 = x0 + segw
        pts = [(x0, y0), (x1, y0), (x1 + tip, y0 + bh / 2), (x1, y0 + bh), (x0, y0 + bh)]
        if k:
            pts.append((x0 + tip, y0 + bh / 2))
        o += poly(pts, fills[k])
    for k, (lb, icn, ti, de) in enumerate(ss):
        ccx = L + k * segw + segw / 2 + (tip / 2 if k else 0)
        o += t(ccx, y0 + bh / 2 + 11, lb, fit(lb or "", segw - 60, 30, 700, 18), 700, WHITE if fills[k] == ACC else INK, "middle")
        colx = L + k * (ZW / n) + ZW / n / 2
        if k:
            o += dash_v(L + k * ZW / n, y0 + bh + 56, min(bottom - 10, y0 + bh + 290))
        yy = y0 + bh + 48
        if icn:
            o += ic(icn, colx - 28, yy, 56, ACC)
            yy += 92
        else:
            yy += 24
        o += t(colx, yy, ti, fit(ti or "", ZW / n - 24, 21, 700, 15), 700, ACC, "middle")
        o += tl(colx, yy + 38, wrap(de or "", ZW / n - 40, 16)[:3], 16, 400, BODY, "middle", lh=1.6)
    return o


def L_toc(top, bottom, items=()):
    """목차 (PDF p2): 01–06 번호 + 제목 + 설명, 3열 그리드(2행은 가운데 정렬)."""
    its = [_item(i, "title", "desc") for i in items][:6]
    n = len(its)
    per = 3 if n in (3, 5, 6) or n > 4 else (2 if n == 4 else n)
    rows = [its[i:i + per] for i in range(0, n, per)]
    colw = ZW / per
    rh = (bottom - top) / max(len(rows), 1)
    o = ""
    k = 0
    for ri, row in enumerate(rows):
        y = top + ri * rh + (rh - 150) / 2
        x0 = L + (ZW - colw * len(row)) / 2
        for ci, (ti, de) in enumerate(row):
            k += 1
            ccx = x0 + colw * (ci + 0.5)
            o += t(ccx, y + 40, f"{k:02d}", 38, 600, ACC, "middle")
            o += t(ccx, y + 86, ti, fit(ti or "", colw - 24, 24, 700, 17), 700, INK, "middle")
            o += tl(ccx, y + 120, wrap(de or "", colw - 32, 15)[:2], 15, 400, BODY, "middle", lh=1.55)
    return o


def L_image_grid(top, bottom, images=()):
    """이미지 페이지 (PDF p9): 1장=전체, 2장=좌우, 3장=큰 1 + 작은 2."""
    ims = list(images) or [None, None, None]
    h = bottom - top
    if len(ims) == 1:
        return img(ims[0], L, top, ZW, h)
    if len(ims) == 2:
        w = (ZW - 16) / 2
        return img(ims[0], L, top, w, h) + img(ims[1], L + w + 16, top, w, h)
    bw = 472
    sw = ZW - bw - 16
    sh = (h - 16) / 2
    return img(ims[0], L, top, bw, h) + img(ims[1], L + bw + 16, top, sw, sh) + img(ims[2], L + bw + 16, top + sh + 16, sw, sh)


def L_quiz(top, bottom, question="", options=("O", "X"), answer=None, label="Q."):
    """퀴즈 (강의용 추가): 질문 카드 + 보기. options가 O/X면 큰 타일, 아니면 번호 보기 목록.
    answer = 정답 보기(문자열 또는 1부터 시작하는 번호) — 지정하면 정답 강조(해설 슬라이드용)."""
    ql = wrap(question, ZW - 140, 24, 700)[:3]
    qh = 48 + len(ql) * 36
    o = r(L, top, ZW, qh, SOFT, rx=20)
    o += t(L + 36, top + 24 + 36, label, 34, 800, ACC)
    o += tl(L + 100, top + 24 + 32, ql, 24, 700, INK, lh=1.5)
    opts = list(options)
    ans = None
    if answer is not None:
        ans = (int(answer) - 1) if str(answer).isdigit() and len(opts) > 1 and str(answer) not in opts else (opts.index(answer) if answer in opts else None)
    y = top + qh + 28
    if [str(x).upper() for x in opts] == ["O", "X"]:
        tw = (ZW - 40) / 2
        th = bottom - y
        for k, s in enumerate(opts):
            x = L + k * (tw + 40)
            hl = ans == k
            o += r(x, y, tw, th, ACC if hl else WHITE, rx=20, stroke=ACC, sw=2)
            if s.upper() == "O":
                o += circ(x + tw / 2, y + th / 2, min(th, tw) * 0.28, ACC if hl else WHITE, WHITE if hl else ACC, 16)
            else:
                d = min(th, tw) * 0.24
                c = WHITE if hl else ACC
                o += ln(x + tw / 2 - d, y + th / 2 - d, x + tw / 2 + d, y + th / 2 + d, c, 16)
                o += ln(x + tw / 2 - d, y + th / 2 + d, x + tw / 2 + d, y + th / 2 - d, c, 16)
        return o
    n = len(opts) or 1
    gap = 14
    oh = min(64, (bottom - y - gap * (n - 1)) / n)
    for k, s in enumerate(opts):
        hl = ans == k
        o += r(L, y, ZW, oh, ACC if hl else WHITE, rx=oh / 2, stroke=ACC, sw=1.5)
        o += circ(L + oh / 2 + 6, y + oh / 2, oh / 2 - 12, WHITE if hl else BAND)
        o += t(L + oh / 2 + 6, y + oh / 2 + 7, str(k + 1), 18, 700, ACC, "middle")
        o += t(L + oh + 24, y + oh / 2 + 7, s, fit(str(s), ZW - oh - 48, 19, 500, 14), 500, WHITE if hl else INK)
        y += oh + gap
    return o


def L_table(top, bottom, header=(), rows=(), widths=None, highlight=None):
    """표 (강의용 추가): 액센트 헤더 + 줄무늬 행. widths = 열 비율. highlight = 강조할 행 번호(1부터)."""
    nc = len(header) or (len(rows[0]) if rows else 1)
    ws = widths or [1] * nc
    tot = sum(ws)
    cws = [ZW * w / tot for w in ws]
    xs = [L + sum(cws[:i]) for i in range(nc)]
    hh, fs = 56, 17
    need = []
    for row in rows:
        mx = max(len(wrap(str(c), w - 28, fs)[:3]) for c, w in zip(row, cws))
        need.append(max(56, 28 + mx * 25))
    avail = bottom - top - hh
    scale = avail / max(sum(need), 1)
    if scale < 1:
        warn("table rows compressed to fit — consider splitting the table")
    scale = min(scale, 76 / min(need), 1.45)          # grow rows to use the space, but not into slabs
    total = hh + sum(need) * scale
    y = top + max((bottom - top - total) / 2, 0)
    o = r(L, y, ZW, hh, ACC, rx=8)
    for x, w, h in zip(xs, cws, header):
        o += _cell_text(x + w / 2, y + hh / 2, h, w - 24, 17, 700, WHITE, maxl=1)
    y += hh
    for i, (row, rh) in enumerate(zip(rows, need)):
        rh *= scale
        hl = highlight == i + 1
        fill = PH if hl else (SOFT if i % 2 else WHITE)
        o += r(L, y, ZW, rh, fill)
        for j, (x, w, c) in enumerate(zip(xs, cws, row)):
            o += _cell_text(x + w / 2, y + rh / 2, str(c), w - 28, fs, 700 if j == 0 else 400, INK, maxl=3)
        y += rh
        o += ln(L, y, R, y, MID, 1)
    return o


LAYOUTS = {
    "statement": (L_statement, "insight"),
    "bullets": (L_bullets, "structure"),
    "text_image": (L_text_image, "visual"),
    "two_col": (L_two_col, "compare"),
    "stats": (L_stats, "data"),
    "cards": (L_cards, "breakdown"),
    "points": (L_points, "breakdown"),
    "keywords": (L_keywords, "insight"),
    "chart": (L_chart, "data"),
    "process": (L_process, "process"),
    "steps": (L_steps, "process"),
    "before_after": (L_before_after, "compare"),
    "cause_result": (L_cause_result, "insight"),
    "timeline": (L_timeline, "process"),
    "toc": (L_toc, "structure"),
    "image_grid": (L_image_grid, "visual"),
    "quiz": (L_quiz, "breakdown"),
    "table": (L_table, "compare"),
}
SHELLS = ("cover", "chapter", "ending")
