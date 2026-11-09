"""ilkit.sv — Insightlearning SVG primitives + shell pages (cover / content page / ending).

All coordinates follow the Insightlearning content shell (1280×720):
  section label y=62 · double navy rule y=72–78 · centered headline 29.6/800 at y=128
  optional lead y=158 · content area y≈184–640 · GM line y=680 · page number y=696.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[5])  # ilkit→scripts→generic-redesign→skills→.claude→repo
_venv = os.path.join(ROOT, ".venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join(ROOT, ".venv", "bin", "python3")
PY = _venv if os.path.exists(_venv) else sys.executable

F = "Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif"
OUT = None  # svg_output dir — set by kit.init(project)

NAVY, SOFT, CARD, TEXT, MUTED, CAPTION, LINE, SKY = "#012281", "#E0EDF3", "#F8F8F8", "#1A1A1A", "#595959", "#666666", "#DFDFDF", "#58CCFF"


def t(x, y, s, fs=15.2, fw=400, fill="#1A1A1A", anchor=None, ls=None):
    a = f' text-anchor="{anchor}"' if anchor else ''
    l = f' letter-spacing="{ls}"' if ls is not None else ''
    return f'  <text x="{x}" y="{y}" font-family="{F}" font-size="{fs}" font-weight="{fw}"{l}{a} fill="{fill}">{s}</text>\n'


def r(x, y, w, h, fill="#F8F8F8", rx=None, op=None):
    a = f' rx="{rx}"' if rx else ''
    o = f' fill-opacity="{op}"' if op is not None else ''
    return f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{a}{o}/>\n'


def ln(x1, y1, x2, y2, c="#DFDFDF", w=1):
    return f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}"/>\n'


def ic(name, x, y, s=24, c="#012281"):
    """Tabler outline icon placeholder — finalize_svg.py embeds it. Check the name exists in assets/icons/tabler-outline/."""
    return (f'  <use data-icon="tabler-outline/{name}" x="{x}" y="{y}" width="{s}" height="{s}" '
            f'fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>\n')


def _write(fname, parts):
    if not OUT:
        raise RuntimeError("sv.OUT is not set — call kit.init(project) first")
    with open(os.path.join(OUT, fname), 'w', encoding='utf-8') as f:
        f.write(''.join(parts))


def page(fname, label, title, gm, num, body, lead=None):
    """Light content page. label 'NN | 섹션', title = so-what headline, gm = governing message (not a title restatement)."""
    o = ['<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">\n',
         '  <rect width="1280" height="720" fill="#FFFFFF"/>\n',
         t(56, 62, label, 24, 300, ls=-0.48),
         '  <rect x="56" y="72" width="136" height="6" fill="#012281"/>\n',
         ln(192, 76, 1224, 76, "#012281", 2),
         t(640, 128, title, 29.6, 800, anchor="middle", ls=-0.89)]
    if lead:
        o.append(t(640, 158, lead, 15.2, 400, "#595959", anchor="middle"))
    o.append(body)
    o.append(t(640, 680, gm, 15.2, 700, "#595959", anchor="middle"))
    o.append(t(1224, 696, f"{num:02d}", 12.8, 400, "#666666", anchor="end"))
    o.append('</svg>\n')
    _write(fname, o)


def cover(eyebrow, l1, l2, lead, foot, fname="01_cover_표지.svg"):
    """Navy cover shell. Filename MUST contain 'cover'."""
    _write(fname, ['<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">\n',
        '  <rect width="1280" height="720" fill="#012281"/>\n',
        '  <polygon points="836,0 1280,0 1280,720 1060,720" fill="#1F375D"/>\n',
        '  <polygon points="824,0 836,0 1060,720 1048,720" fill="#58CCFF"/>\n',
        '  <image href="../images/insightlearning-logo-white.png" x="56" y="48" width="200" height="28" preserveAspectRatio="xMinYMid meet"/>\n',
        t(56, 232, eyebrow, 17.6, 400, "#58CCFF", ls=7),
        t(56, 316, l1, 52, 700, "#FFFFFF", ls=-1.56),
        t(56, 380, l2, 52, 700, "#FFFFFF", ls=-1.56) if l2 else '',
        t(56, 440, lead, 17.6, 400, "#FFFFFF"),
        t(56, 656, foot, 15.2, 400, "#D2D6E3"), '</svg>\n'])


CONTACTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "contacts.local.txt")
CONTACT_PLACEHOLDER = "담당자 · 연락처 · 이메일"


def load_contacts():
    """Ending-slide contacts — never committed (the repo may be public).
    Source order: env GR_CONTACTS ('이름 직함 · 전화 · 메일|…') → generic-redesign/contacts.local.txt (one per line)."""
    env = os.environ.get("GR_CONTACTS", "").strip()
    if env:
        return [c.strip() for c in env.split("|") if c.strip()]
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
    return []


CONTACTS = load_contacts()


def ending(accent, foot, fname, contacts=CONTACTS):
    """Navy ending shell. Filename MUST contain 'ending'."""
    o = ['<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">\n',
         '  <rect width="1280" height="720" fill="#012281"/>\n',
         '  <rect x="240" y="104" width="800" height="512" fill="none" stroke="#58CCFF" stroke-width="8"/>\n',
         '  <image href="../images/insightlearning-logo-white.png" x="540" y="160" width="200" height="28" preserveAspectRatio="xMidYMid meet"/>\n',
         t(640, 236, "THANK YOU", 17.6, 400, "#58CCFF", anchor="middle", ls=7),
         t(640, 316, "감사합니다", 56, 800, "#FFFFFF", anchor="middle", ls=-1.68),
         t(640, 376, accent, 40, 800, "#58CCFF", anchor="middle", ls=-0.8),
         t(640, 440, "인싸이트러닝㈜ · 경기도 성남시 분당구 황새울로200번길 36 동부루트빌딩 504-505호", 15.2, 400, "#D2D6E3", anchor="middle"),
         t(640, 466, "Tel. 070-7516-0770 · Fax. 0303-3440-0806 · insighthrd.com", 15.2, 400, "#D2D6E3", anchor="middle"),
         '  <line x1="560" y1="492" x2="720" y2="492" stroke="#58CCFF" stroke-width="2"/>\n']
    if not contacts:
        print("[WARN] no ending contacts configured (GR_CONTACTS or generic-redesign/contacts.local.txt) — "
              f"placeholder '{CONTACT_PLACEHOLDER}' used; ask the user for the contact lines")
        contacts = [CONTACT_PLACEHOLDER]
    for i, c in enumerate(contacts):
        o.append(t(640, 528 + i * 26, c, 15.2, 400, "#FFFFFF", anchor="middle"))
    o += [t(640, 672, foot, 12.8, 400, "#D2D6E3", anchor="middle"), '</svg>\n']
    _write(fname, o)


def check(project, *names):
    """Run svg_quality_checker on each SVG; print OK or the WARN/ERROR lines."""
    for n in names:
        res = subprocess.run([PY, os.path.join(ROOT, ".claude", "skills", "slide", "scripts", "svg_quality_checker.py"),
                              os.path.join(ROOT, "output", project, "svg_output", n)],
                             capture_output=True, text=True, encoding="utf-8", errors="replace",
                             env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        lines = [l for l in res.stdout.splitlines()
                 if (l.strip().startswith("[WARN]") and "with warnings" not in l.lower() and "quiet zone" not in l)
                 or ("[ERROR]" in l and "With errors" not in l)]
        print(n, "OK" if not lines else "\n  ".join(lines))
