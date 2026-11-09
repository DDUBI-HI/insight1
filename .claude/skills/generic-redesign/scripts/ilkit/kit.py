"""ilkit.kit — project bootstrap + reusable Insightlearning content blocks for generic-redesign decks.

Usage in a build script (one per deck, kept at output/<project>/build.py):

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(".claude/skills/generic-redesign/scripts/ilkit").resolve()))
    from kit import *

    P = "ai_b2b_sales_generic"
    init(P, images=[(r"<workdir>/img/inst_kim.jpg", "inst_kim.jpg")])
    plan(P, title, goal, source_name, rows, length_reason, arc)
    cover(...); page(...); ...; ending(...)
    notes(P, [(stem, text), ...]); checkall(P)

Every block returns an SVG fragment string (body) that you pass to page(). Coordinates assume
the content area x=96–1184, y=184–632 (see references/layout-kit.md).
"""
import os
import shutil
import subprocess
import textwrap

import sv
from sv import *          # t r ln ic page cover ending check ROOT PY CONTACTS + colour constants
from blocks import *      # chevrons dot modgrid budget roster timetable modrows
from planlib import slide, write_plan, write_spec

SK = os.path.join(ROOT, ".claude", "skills", "slide")
LAYOUT = os.path.join(SK, "templates", "layouts", "insightlearning")
_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


# ─────────────────────────── project bootstrap ───────────────────────────

def init(proj, images=()):
    """Create output/<proj> (project_manager init), copy layout templates + brand logos,
    copy images [(src_path, dst_name)], and point sv.OUT at its svg_output/."""
    P = os.path.join(ROOT, "output", proj)
    if not os.path.isdir(os.path.join(P, "templates")):
        subprocess.run([PY, os.path.join(SK, "scripts", "project_manager.py"), "init", proj, "--format", "ppt169"],
                       cwd=ROOT, capture_output=True, env=_ENV)
    for d in ("templates", "images", "svg_output", "svg_final", "notes", "exports", "sources"):
        os.makedirs(os.path.join(P, d), exist_ok=True)   # also covers a pre-created folder holding build.py
    for f in os.listdir(LAYOUT):
        if f.endswith(".svg") or f == "design_spec.md":
            shutil.copy(os.path.join(LAYOUT, f), os.path.join(P, "templates", f))
    for f in ("insightlearning-logo-white.png", "insightlearning-logo-color.png"):
        shutil.copy(os.path.join(LAYOUT, "assets", "brand", f), os.path.join(P, "images", f))
    for src, dst in images:
        shutil.copy(src, os.path.join(P, "images", dst))
    sv.OUT = os.path.join(P, "svg_output")
    os.makedirs(sv.OUT, exist_ok=True)
    return P


def plan(proj, title, goal, srcname, rows, length_reason, arc, audience="고객사 HRD 담당자 (범용)"):
    """Write + validate slide_plan.json (R1–R5) and design_spec.md.
    rows: [(slide_role, layout_family, working_title, core_message, page_family)]
      slide_role ∈ cover context problem insight evidence solution roadmap comparison team pricing summary appendix cta
      layout_family ∈ structure insight breakdown compare data process visual ; page_family ∈ title body end"""
    S = []
    for i, (ro, fa, ti, co, pg) in enumerate(rows, 1):
        tb = None if pg != "body" or fa in ("process", "visual") else f"{ti}의 핵심 정보를 표로 정리합니다"
        blocks = [("table" if tb else ("diagram_flow" if fa == "process" else ("image" if fa == "visual" else "title")), ti, co)]
        S.append(slide(i, ro, fa, ti, co, co, f"{ti} — 흐름상 {i}번째에 배치해 앞 장의 내용을 이어받는다 (원본 구성 기반 재편)",
                       blocks, page=pg, table=tb))
    P = os.path.join(ROOT, "output", proj)
    write_plan(os.path.join(P, "slide_plan.json"),
               {"working_title": title, "deck_goal": goal, "deck_type": "proposal", "target_audience": audience,
                "tone": "formal 합니다체", "target_length": {"slides": len(rows), "reasoning": length_reason}},
               {"narrative_shape": arc, "why_this_order_is_persuasive": "필요성 → 구조 → 상세 → 운영 조건 순으로 의사결정을 돕는다"},
               [{"source_id": "src_01", "source_type": "file", "summary": srcname, "relevance": "high", "usable_for": ["all"]}], S)
    res = subprocess.run([PY, os.path.join(ROOT, ".claude", "skills", "slide-plan", "scripts", "validate_plan.py"),
                          os.path.join(P, "slide_plan.json")],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=_ENV)
    out = [l for l in (res.stdout + res.stderr).splitlines() if "ERROR" in l or "OK" in l or "FAIL" in l]
    print(out)
    if any("FAIL" in l for l in out):
        raise SystemExit("slide_plan.json failed validation — fix the rows above")
    write_spec(P, proj, audience, [("instructor / reference images", "-", "-", "강사 · 예시", "Photography")], [("icons", "various", "-")])


def notes(proj, items):
    """items: [(svg_stem, script)] — one per slide, stems must match SVG names. Use '[전환]' on slides 2+."""
    P = os.path.join(ROOT, "output", proj)
    with open(os.path.join(P, "notes", "total.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(f"# {k}\n\n{v}\n\n소요 시간: 1분\n" for k, v in items))


def checkall(proj):
    import glob
    check(proj, *[os.path.basename(f) for f in sorted(glob.glob(os.path.join(ROOT, "output", proj, "svg_output", "*.svg")))])


# ─────────────────────────── text helpers ───────────────────────────

def wo(s, op):
    """Apply fill-opacity to white text/rects (use instead of rgba)."""
    return s.replace('fill="#FFFFFF"', f'fill="#FFFFFF" fill-opacity="{op}"')


def text_w(s, fs=12.8):
    """Rough rendered width: Hangul ≈ 1em, ASCII ≈ 0.55em, brackets/dots/spaces ≈ 0.33em."""
    return sum(fs if ord(c) > 0x1100 else (fs * 0.33 if c in "[]·() " else fs * 0.58) for c in s)


def wrap(s, n):
    return textwrap.wrap(s, n)


def tagline(x, y, s, fs=12.8):
    """'[실습 · 공유] 내용' → navy bold tag + body text, spaced by measured width."""
    if s.startswith("["):
        tg, rest = s[1:].split("]", 1)
        tag = f"[{tg}]"
        return t(x, y, tag, fs, 700, "#012281") + t(round(x + text_w(tag, fs) + 8, 1), y, rest.strip(), fs, 400)
    return t(x, y, s, fs, 400)


def bullets(X, y, items, fs=13.6, gap=26, color="#1A1A1A"):
    b = ''
    for i, s in enumerate(items):
        b += dot(X + 4, y + i * gap - 5) + t(X + 16, y + i * gap, s, fs, 400, color)
    return b


# ─────────────────────────── layout blocks ───────────────────────────

def info_panel(rows, eyebrow="PROGRAM | 과정 정보", x=96, w=400, top=184, h=448):
    """Navy left panel: rows [(label, value | [lines])]."""
    b = r(x, top, w, h, "#012281")
    b += wo(t(x + 32, top + 38, eyebrow, 12.8, 600, "#FFFFFF", ls=0.26), 0.7)
    gap = (h - 84) / max(len(rows), 1)
    for i, (k, v) in enumerate(rows):
        y = top + 84 + i * gap
        b += wo(t(x + 32, y, k, 12.8, 600, "#FFFFFF"), 0.7)
        lines = v if isinstance(v, list) else [v]
        for j, s in enumerate(lines):
            b += t(x + 32, y + 26 + j * 22, s, 15.2, 700 if j == 0 else 400, "#FFFFFF")
    return b


def numlist(X, top, items, width=648, gap=70, eyebrow=None):
    """Numbered list 01/02/…: items [(title, desc)] separated by hairlines."""
    b = ''
    y0 = top
    if eyebrow:
        b += t(X, top + 12, eyebrow, 12.8, 600, "#595959", ls=0.26)
        y0 = top + 28
    for i, (a, c) in enumerate(items):
        y = y0 + i * gap
        b += ln(X, y, X + width, y) + t(X, y + 30, f"0{i+1}", 15.2, 700, "#012281") + t(X + 40, y + 30, a, 15.2, 700)
        if c:
            b += t(X + 40, y + 54, c, 13.6, 400, "#595959")
    b += ln(X, y0 + len(items) * gap, X + width, y0 + len(items) * gap)
    return b


def qgrid(Q, hl=None, width=34):
    """2×3 question cards (사전 설문 / 사전 점검): Q [(title, question)]."""
    b = ''
    for i, (a, c) in enumerate(Q):
        col = i % 2; row = i // 2; x = 96 + col * 552; y = 184 + row * 144
        b += r(x, y, 536, 128, "#E0EDF3" if i == hl else "#F8F8F8", 14)
        b += t(x + 24, y + 40, f"Q{i+1}", 17.6, 800, "#012281") + t(x + 68, y + 40, a, 15.2, 700)
        for j, s in enumerate(textwrap.wrap(c, width)[:2]):
            b += t(x + 24, y + 78 + j * 24, s, 13.6, 400, "#1A1A1A" if i == hl else "#595959")
    return b


def cards(items, top=184, h=448, hl=None, header_h=88):
    """N equal columns with navy header: items [(eyebrow, title, sub, body_fn(x, y, w) -> svg)]."""
    n = len(items); gap = 16; w = (1088 - gap * (n - 1)) / n
    b = ''
    for k, (ey, ti, sub, fn) in enumerate(items):
        x = round(96 + k * (w + gap))
        b += r(x, top, round(w), header_h, "#012281") + wo(t(x + 24, top + 28, ey, 12.8, 600, "#FFFFFF", ls=0.26), 0.7)
        b += t(x + 24, top + 56, ti, 17.6, 700, "#FFFFFF")
        if sub:
            b += wo(t(x + 24, top + 78, sub, 13.6, 400, "#FFFFFF"), 0.8)
        b += r(x, top + header_h, round(w), h - header_h, "#E0EDF3" if k == hl else "#F8F8F8")
        if fn:
            b += fn(x, top + header_h, round(w))
    return b


def tablerows(cols, head, rows, top=184, rh=56, hl=None, fs=15.2):
    """Table with navy label column. cols [(x, w)], head [labels], rows [[label|[lines], cell|[lines], …]].
    rh may be an int or a per-row list. Returns (svg, bottom_y)."""
    x0, w0 = cols[0]
    b = r(x0, top, w0, 48, "#012281") + t(x0 + w0 / 2, top + 30, head[0], 15.2, 700, "#FFFFFF", anchor="middle")
    xe = cols[-1][0] + cols[-1][1]
    b += r(cols[1][0], top, xe - cols[1][0], 48, "#F8F8F8")
    for (x, w), h in zip(cols[1:], head[1:]):
        b += t(x + 16, top + 30, h, 15.2, 700)
    y = top + 48
    for i, row in enumerate(rows):
        hh = rh if not isinstance(rh, list) else rh[i]
        b += r(x0, y, w0, hh, "#012281", op=0.7) + ln(x0, y, x0 + w0, y, "#FFFFFF")
        lab = row[0] if isinstance(row[0], list) else [row[0]]
        for j, s in enumerate(lab):
            b += t(x0 + w0 / 2, y + hh / 2 + 5 - (len(lab) - 1) * 10 + j * 20, s, 15.2 if len(lab) == 1 else 13.6, 700, "#FFFFFF", anchor="middle")
        if hl == i:
            b += r(cols[1][0], y, xe - cols[1][0], hh, "#E0EDF3")
        for (x, w), cell in zip(cols[1:], row[1:]):
            lines = cell if isinstance(cell, list) else [cell]
            for j, s in enumerate(lines):
                b += t(x + 16, y + hh / 2 + 5 - (len(lines) - 1) * 10 + j * 20, s, fs if len(lines) == 1 else 12.8, 400, "#1A1A1A")
        y += hh
        b += ln(cols[1][0], y, xe, y)
    return b, y


def profile_one(img, name, title, now, sections_l, sections_r, tag=None):
    """Single instructor page: photo card (images/<img>) + two text columns of [(label, [lines])]."""
    b = r(96, 184, 216, 448, "#F8F8F8", 14)
    b += f'  <image href="../images/{img}" x="112" y="200" width="184" height="245" preserveAspectRatio="xMidYMid slice"/>\n'
    b += t(112, 482, name, 22, 800, ls=-0.5) + t(112 + 22 * len(name) + 10, 482, title, 15.2, 700, "#595959")
    for j, s in enumerate(now):
        b += t(112, 512 + j * 22, s, 12.8, 400, "#595959")
    if tag:
        b += r(112, 592, 184, 28, "#E0EDF3", 6) + t(124, 611, tag, 12.8, 700)
    for X, secs in ((344, sections_l), (776, sections_r)):
        y = 196
        for lab, lines in secs:
            b += t(X, y, lab, 12.8, 600, "#012281", ls=0.26) + ln(X, y + 8, X + 408, y + 8)
            for j, s in enumerate(lines):
                b += t(X, y + 32 + j * 21, s, 13.6, 400)
            y += 32 + 21 * len(lines) + 18
    return b


def budget_unit(rows, hero, hero_label, stats, formula, note):
    """Generic budget page (unit price + 산정 방식, no client total).
    rows [(구분, 단가, 산출 기준, 비고, highlight)] · stats [(value, label)]×3 ·
    formula [(value, label) | ("×"|"=", None)] · note: '※ 1차수 기준 ○○원(VAT 별도) · …'"""
    b = r(96, 184, 400, 288, "#012281")
    b += wo(t(128, 224, "PRICING | 산출 기준", 12.8, 600, "#FFFFFF", ls=0.26), 0.7)
    b += t(128, 280, hero, 40, 800, "#FFFFFF", ls=-0.8)
    b += wo(t(128, 308, hero_label, 15.2, 400, "#FFFFFF"), 0.8)
    b += ln(128, 332, 464, 332, "#FFFFFF").replace('/>', ' stroke-opacity="0.3"/>')
    for i, (v, l) in enumerate(stats):
        y = 368 + i * 40
        b += t(128, y, v, 17.6, 700, "#FFFFFF") + wo(t(464, y, l, 15.2, 400, "#FFFFFF", anchor="end"), 0.8)
    b += t(544, 196, "UNIT PRICE | 항목별 단가 (VAT 별도)", 12.8, 600, "#595959", ls=0.26)
    b += r(544, 208, 640, 56, "#F8F8F8")
    for x, s, a in [(568, "구분", None), (720, "단가", None), (880, "산출 기준", None), (1160, "비고", "end")]:
        b += t(x, 241, s, 15.2, 700, anchor=a)
    rh = min(56, int(208 / len(rows)))
    y = 264
    for g, u, base, note_, hl in rows:
        if hl:
            b += r(544, y, 640, rh, "#E0EDF3")
        b += t(568, y + rh / 2 + 5.5, g, 15.2, 700) + t(720, y + rh / 2 + 5.5, u, 15.2, 700 if hl else 400)
        b += t(880, y + rh / 2 + 5.5, base, 12.8, 400, "#595959") + t(1160, y + rh / 2 + 5.5, note_, 12.8, 400, "#666666", anchor="end")
        y += rh
        b += ln(544, y, 1184, y)
    b += r(96, 496, 1088, 112, "#F8F8F8", 14)
    b += t(128, 530, "HOW IT ADDS UP | 교육비 산정 방식", 12.8, 600, "#595959", ls=0.26)
    n = len(formula); xs = [200 + i * (880 / (n - 1)) for i in range(n)]
    for x, (v, l) in zip(xs, formula):
        x = round(x)
        if l is None:
            b += t(x, 572, v, 17.6, 400, "#595959", anchor="middle")
        else:
            b += t(x, 566, v, 17.6, 700, anchor="middle") + t(x, 590, l, 12.8, 400, "#666666", anchor="middle")
    b += t(96, 634, note, 12.8, 400, "#666666")
    return b
