#!/usr/bin/env python3
"""make_design_pdf.py — render the edu-video design system as a 16:9 PDF.

Usage (repo root, after the sample deck is built through svg_to_pptx so svg_final/ exists):
    .claude/skills/slide/scripts/_py.sh .claude/skills/edu-video/scripts/make_design_pdf.py [output/edu_video_privacy_sample]

Writes output/_design_pdf/design-system.html, then prints it to
.claude/skills/edu-video/design-system.pdf with Node Playwright (Chromium). Without Playwright, open the
HTML in Chrome → 인쇄 → PDF로 저장 (용지: 사용자 지정 1280×720px, 여백 없음, 배경 그래픽 켬).
Slide previews are the real svg_final pages inlined as vector SVG.
"""
import glob
import html
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE / "evkit"))
import ev  # noqa: E402
import illust  # noqa: E402

PROJ = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "output" / "edu_video_privacy_sample"
FINAL = PROJ / "svg_final"
OUTD = ROOT / "output" / "_design_pdf"
PDF = SKILL / "design-system.pdf"
VERSION = "v1.0"

if not FINAL.is_dir():
    sys.exit(f"{FINAL} missing — build the sample deck first (SKILL.md steps 2–3)")
PAGES = {Path(p).name.split("_")[0]: p for p in sorted(glob.glob(str(FINAL / "*.svg")))}


def slide_svg(num, width, silhouette=False):
    s = open(PAGES[f"{num:02d}"], encoding="utf-8").read()
    s = re.sub(r"<\?xml[^>]*>\s*", "", s)

    def fix(m):  # PPTX keeps icon strokes at 2px regardless of scale — mirror that in the preview
        k = float(m.group(2))
        return m.group(0).replace('stroke-width="2"', f'stroke-width="{round(2 / k, 3)}"')
    s = re.sub(r'<g transform="translate\(([^)]*)\) scale\(([\d.]+)\)"[^>]*stroke-width="2"[^>]*>', fix, s)
    s = re.sub(r'<svg ([^>]*?)width="1280" height="720"',
               lambda m: f'<svg {m.group(1)}width="{width}" height="{round(width * 9 / 16)}"', s, count=1)
    if silhouette:
        s = s.replace("</svg>", SIL + "</svg>")
    return s


SIL = ('<g><circle cx="1090" cy="292" r="64" fill="#9AA6C8"/>'
       '<path d="M930 720 C930 520 994 410 1090 410 C1186 410 1250 520 1250 720 Z" fill="#9AA6C8"/>'
       '<text x="1090" y="600" font-family="Pretendard" font-size="30" font-weight="700" fill="#FFFFFF" text-anchor="middle">강사 영상</text></g>')


def contrast(a, b):
    def lum(h):
        r, g, b_ = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b_)
    x, y = sorted([lum(a), lum(b)], reverse=True)
    return (x + 0.05) / (y + 0.05)


def page(label, title, body, n, dark=False, cls=""):
    return f'''<section class="pg {'dark' if dark else ''} {cls}">
  <header>{f'<span class="lab">{label}</span>' if label else ''}<h1>{title}</h1></header>
  <div class="body">{body}</div>
  <footer><span>Insightlearning · 교육 영상 배경 PPT 디자인 시스템 {VERSION}</span><span>{n:02d}</span></footer>
</section>'''


def ill_svg(name, size=150, dark=False):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 240 240">{illust.draw(name, 0, 0, 240, dark)}</svg>')


# ───────────────────────────── pages ─────────────────────────────
P = []

# 1 cover
P.append(f'''<section class="pg cover">
  <div class="cv-l">
    <img class="logo" src="{(ROOT / '.claude/skills/slide/templates/layouts/insightlearning/assets/brand/insightlearning-logo-white.png').as_uri()}"/>
    <span class="eyebrow">DESIGN SYSTEM {VERSION}</span>
    <h1>교육 영상<br/>배경 PPT<br/>디자인 시스템</h1>
    <p>강사 합성용 70 / 30 화면 · 저시력 배려 큰 글씨 · 네이비 라인 일러스트<br/>원고를 넣으면 바로 PPT로 — <b>/edu-video</b></p>
    <span class="date">{date.today().strftime('%Y.%m')}</span>
  </div>
  <div class="cv-r"><div class="frame">{slide_svg(5, 660, True)}</div>
    <div class="cap">실제 화면 예시 — 오른쪽 30%에 강사 영상이 들어갑니다</div></div>
</section>''')

# 2 principles
pr = [("layout-sidebar-right", "70 / 30 화면 분할", "왼쪽 70%는 콘텐츠, 오른쪽 30%는 강사 영역으로 비워 둡니다. 하단 76px는 자막 자리입니다.",
       "x 896–1280 · y 644–720"),
      ("text-size", "큰 글씨가 기본", "저시력 학습자를 기준으로 합니다. 본문 24pt, 가장 작은 글자도 21pt이고 대비는 6.6:1 이상입니다.",
       "최소 28px = 21pt"),
      ("focus-2", "한 화면 한 메시지", "항목은 4개, 항목마다 2줄까지만 씁니다. 화면마다 핵심 한 줄로 '그래서 무엇인지'를 남깁니다.",
       "항목 ≤ 4 · 2줄"),
      ("brush", "라인 일러스트", "네이비 3px 선과 연한 블롭으로 그린 일러스트 20종입니다. 스톡 사진·클립아트·회색 목업은 쓰지 않습니다.",
       "편집 가능한 도형")]
cards = "".join(f'''<div class="pc"><div class="pc-n">{i + 1:02d}</div><h3>{a}</h3><p>{b}</p><span class="tag">{c}</span></div>'''
                for i, (_, a, b, c) in enumerate(pr))
P.append(page("01 · 원칙", "네 가지 원칙", f'<div class="grid4">{cards}</div>'
              '<div class="note">루트 슬라이드 엔진 규칙을 그대로 지킵니다: 1280×720 · 단일 액센트(네이비 #012281) · 이모지 금지 · 네이티브 SVG→PPTX(편집 가능한 도형) · Pretendard.</div>', 2))

# 3 structure
def zone_svg():
    o = ['<svg width="700" height="394" viewBox="-40 -30 1360 765">',
         '<rect x="0" y="0" width="1280" height="720" fill="#FFFFFF" stroke="#C2C2C2" stroke-width="2"/>',
         f'<rect x="{ev.STAGE_X}" y="0" width="{1280 - ev.STAGE_X}" height="720" fill="#E0EDF3"/>',
         f'<rect x="0" y="{ev.CAPTION_Y}" width="1280" height="{720 - ev.CAPTION_Y}" fill="#595959" fill-opacity="0.16"/>',
         '<rect x="64" y="40" width="210" height="45" rx="22" fill="#E0EDF3"/>',
         '<rect x="64" y="104" width="460" height="46" fill="#012281" fill-opacity="0.14"/>',
         '<line x1="64" y1="168" x2="848" y2="168" stroke="#DFDFDF" stroke-width="2"/><rect x="64" y="166" width="88" height="4" fill="#012281"/>',
         f'<rect x="64" y="{ev.BODY_TOP}" width="784" height="{ev.BODY_BOT - ev.BODY_TOP}" fill="none" stroke="#012281" stroke-width="3" stroke-dasharray="10 8"/>',
         f'<rect x="64" y="{ev.KEY_Y}" width="784" height="{ev.KEY_H}" rx="16" fill="#E0EDF3"/>',
         '<line x1="872" y1="0" x2="872" y2="720" stroke="#E11D48" stroke-width="2" stroke-dasharray="6 6"/>']
    lab = lambda x, y, s, c="#012281", a="start", fs=26: f'<text x="{x}" y="{y}" font-family="Pretendard" font-size="{fs}" font-weight="700" fill="{c}" text-anchor="{a}">{s}</text>'  # noqa: E731
    o += [lab(84, 72, "라벨 pill", fs=22), lab(84, 137, "제목 44px · 한 줄", fs=24),
          lab(456, 384, "본문 영역  y 196–552", a="middle", fs=30), lab(456, 418, "x 64–848 · 폭 784", "#595959", "middle", 24),
          lab(456, 606, "핵심 한 줄 (GM)  y 568–628 · 30px", a="middle", fs=24),
          lab(640, 692, "자막 안전 영역  y 644–720 — 비움", "#1A1A1A", "middle", 26),
          lab(1088, 300, "강사 영역", "#012281", "middle", 34), lab(1088, 342, "x 896–1280 · 30%", "#595959", "middle", 24),
          lab(1088, 374, "비움", "#595959", "middle", 24),
          lab(880, 28, "안전선 x 872", "#E11D48", "start", 20),
          lab(0, -6, "0", "#595959", "start", 18), lab(1280, -6, "1280", "#595959", "end", 18), lab(-8, 720, "720", "#595959", "end", 18)]
    o.append("</svg>")
    return "".join(o)


rows = [("콘텐츠 영역", "x 64–848", "x 96–1272"), ("안전선 (넘으면 오류)", "x ≤ 872", "x ≤ 1308"), ("강사 영역", "x 896–1280", "x 1344–1920"),
        ("제목 기준선", "y 140", "y 210"), ("본문", "y 196–552", "y 294–828"), ("핵심 한 줄", "y 568–628", "y 852–942"),
        ("자막 안전 영역", "y 644–720", "y 966–1080")]
tbl = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
P.append(page("02 · 화면 구조", "1280×720 캔버스 — 영상 1920×1080에서 1.5배",
              f'<div class="row"><div>{zone_svg()}</div><div class="side"><table class="t nw"><tr><th>영역</th><th>캔버스</th><th>1080p 영상</th></tr>{tbl}</table>'
              '<p class="small">자동 검사(evcheck): 안전선을 넘거나 자막 영역에 들어간 요소, 28px 미만 글자가 있으면 빌드가 멈춥니다.</p></div></div>', 3))

# 4 typography
ty = [("display", 64, 48, 96, "Bold", "개인정보보호"), ("emphasis", 52, 39, 78, "Bold", "알아볼 수 있다면"),
      ("h1 · 제목", 44, 33, 66, "Bold", "개인정보란?"), ("h2 · 정의·질문", 36, 27, 54, "Regular", "사망자의 정보라도"),
      ("body · 본문", 32, 24, 48, "Regular", "얼굴로 개인을 알아볼 수 있습니다"), ("key · 핵심 한 줄", 30, 22.5, 45, "Bold", "결합해서 알아볼 수 있으면"),
      ("min · 최소", 28, 21, 42, "Regular", "라벨 · 보조 설명 전용")]
trs = "".join(f'''<tr><td class="tk">{a}</td><td>{b}px</td><td><b>{c}pt</b></td><td>{d}px</td><td>{e}</td>
<td><span style="font-size:{b * 0.62}px;font-weight:{700 if e == 'Bold' else 400};{'color:#012281;' if 'key' in a else ''}">{f}</span></td></tr>''' for a, b, c, d, e, f in ty)
P.append(page("03 · 타이포그래피", "Pretendard 한 서체, 21pt 미만 금지",
              f'<table class="t ty"><tr><th>토큰</th><th>캔버스</th><th>PPT</th><th>1080p</th><th>굵기</th><th>견본 (62% 축소)</th></tr>{trs}</table>'
              '<div class="note">줄 간격 1.35–1.45 · 본문 한 줄 약 22자 · PPTX 굵기는 Regular/Bold 두 가지 · 빌더가 줄을 균형 있게 나눠 한 단어만 남는 줄을 막습니다 · 강제 줄바꿈은 <code> | </code></div>', 4))

# 5 colour
sw = [("#012281", "네이비 · 액센트", "강조 글자, 번호, 아이콘, 셸 배경"), ("#E0EDF3", "소프트", "라벨, 핵심 띠, 강사 영역, 블롭"),
      ("#1A1A1A", "본문", "모든 본문"), ("#595959", "보조", "설명, X 쪽 머리글"), ("#F8F8F8", "카드 면", "카드, 비교 칸, 퀴즈 보기"),
      ("#FFFFFF", "배경", "콘텐츠 화면"), ("#58CCFF", "스카이", "표지·챕터·엔딩에서만"), ("#1F375D", "잉크", "셸 일러스트 블롭")]
sws = "".join(f'<div class="sw"><div class="chip" style="background:{h};{"border:1px solid #DFDFDF;" if h in ("#FFFFFF", "#F8F8F8") else ""}"></div><b>{n}</b><code>{h}</code><span>{u}</span></div>' for h, n, u in sw)
pairs = [("#1A1A1A", "#FFFFFF"), ("#595959", "#FFFFFF"), ("#012281", "#FFFFFF"), ("#012281", "#E0EDF3"), ("#1A1A1A", "#F8F8F8"),
         ("#595959", "#F8F8F8"), ("#FFFFFF", "#012281"), ("#D2D6E3", "#012281"), ("#58CCFF", "#012281")]
cps = "".join(f'<div class="cp" style="background:{b};color:{a};{"border:1px solid #DFDFDF;" if b in ("#FFFFFF", "#F8F8F8") else ""}"><b>가나 Aa</b><span>{contrast(a, b):.1f} : 1</span></div>' for a, b in pairs)
P.append(page("04 · 컬러", "네이비 하나만 액센트로 — 모든 글자 대비 6.6 : 1 이상",
              f'<div class="sws">{sws}</div><h3 class="h3">글자 · 배경 대비 (WCAG)</h3><div class="cps">{cps}</div>'
              '<p class="small">모든 글자가 21pt 이상이라 WCAG의 \'큰 텍스트\'에 해당합니다. AAA 기준(4.5 : 1)을 모두 넘습니다. 그라디언트, 글로우, 그림자, 테마 밖 색(초록 등)은 쓰지 않습니다.</p>', 5))

# 6 accessibility
acc = [("A1", "모든 글자 28px(21pt) 이상, 본문 32px(24pt) 이상", "자동 검사"), ("A2", "글자와 배경 대비 6.6 : 1 이상", "토큰으로 보장"),
       ("A3", "색으로만 뜻을 전하지 않습니다. 강조는 굵게 + 네이비 + 하이라이트, O/X는 모양으로 구분", "레이아웃 내장"),
       ("A4", "본문 항목은 화면당 4개, 항목당 2줄까지", "넘치면 빌드 중단"), ("A5", "강사 영역·자막 영역에 아무것도 넣지 않습니다", "자동 검사"),
       ("A6", "일러스트 안에 글자를 넣지 않습니다. 일러스트는 장식이고 뜻은 텍스트가 전합니다", "라이브러리 설계"),
       ("A7", "화면의 핵심 문구는 강사가 말로도 읽습니다. 화면을 볼 수 없는 학습자를 위해 발표자 노트에 원고를 넣습니다", "say → 노트"),
       ("A8", "깜빡임·빠른 애니메이션 금지 (1초 3회 이상 깜빡임 금지). 전환은 컷 또는 짧은 페이드", "편집 가이드"),
       ("A9", "가는 선으로 뜻을 전하지 않습니다. 의미 있는 도형은 면이나 4px 이상 선을 씁니다", "레이아웃 내장")]
ar = "".join(f'<tr><td class="tk">{a}</td><td>{b}</td><td class="muted">{c}</td></tr>' for a, b, c in acc)
P.append(page("05 · 접근성", "저시력·시각장애 학습자를 위한 9가지 규칙",
              f'<table class="t acc"><tr><th>#</th><th>규칙</th><th>지키는 방법</th></tr>{ar}</table>', 6))

# 7 illustration library
cells = "".join(f'<div class="il">{ill_svg(n, 132)}<b>{n}</b><span>{html.escape(d.split(" — ")[0])}</span></div>' for n, (_, d) in illust.LIB.items())
P.append(page("06 · 일러스트", "네이비 라인 일러스트 20종 — PowerPoint에서 바로 편집",
              f'<div class="ilg">{cells}</div>', 7, cls="tight"))

# 8 replacement
rep = [("클립아트 정장 남성 (물음표)", "스톡 클립아트 화풍, 다른 그림과 톤이 섞임", "question", "concept"),
       ("스톡 단체 사진", "해상도·초상권 부담, 화면 톤과 안 맞음", "talk", "case"),
       ("회색 모니터 목업 + 빨간 막대", "낡은 기기 표현, 액센트 색 충돌", "laptop", "screen"),
       ("연두 + 네이비 두 가지 액센트", "단일 액센트 원칙 위반", "shield", "모든")]
rr = "".join(f'<tr><td><b>{a}</b><br/><span class="muted">{b}</span></td><td class="arrow">→</td><td class="ic">{ill_svg(c, 96)}</td><td><b>{c}</b><br/><span class="muted">{d} 레이아웃</span></td></tr>' for a, b, c, d in rep)
dk = "".join(f'<div class="dk">{ill_svg(n, 108, True)}</div>' for n in ("graduate", "book", "shield", "checklist", "trophy", "idea"))
P.append(page("06 · 일러스트", "참고 PPT의 옛 요소는 이렇게 바꿨습니다",
              f'<div class="row"><table class="t rep">{rr}</table><div class="side"><h3 class="h3">스타일 규칙</h3><ul class="ul">'
              '<li>네이비 3px 둥근 선 + 흰 면</li><li>연한 블롭 하나 (#E0EDF3)</li><li>반짝이·점·고리 장식 2–3개</li><li>얼굴은 눈·미소만, 성별·나이는 단순하게</li>'
              '<li>네이비 셸 위에서는 흰 선 + 스카이 장식</li></ul><div class="dks">' + dk + '</div></div></div>', 8))

# 9–11 layout catalogue
cat = [(1, "cover", "과정·차시 표지", "eyebrow · title(2줄) · sub · meta · illust"),
       (3, "chapter", "단원 구분 — 번호 자동", "title · sub · illust"),
       (2, "agenda", "학습 순서 2–6개", "items · current(선택)"),
       (5, "concept", "정의 문장 + 강조 구", "lines · emphasis · illust"),
       (4, "quote", "법 조항·정의 인용", "source · text(**강조**)"),
       (6, "bullets", "아이콘 + 항목 2–4개", "items{icon, text, sub}"),
       (7, "compare", "O / X 두 칸 비교", "left · right {title, mark, items}"),
       (9, "cards", "2–3열 카드, 1개 강조", "items{icon, title, text} · highlight"),
       (10, "stat", "큰 숫자 하나", "caption · value · unit · desc"),
       (12, "steps", "2–4단계 흐름", "items{title, text, icon}"),
       (13, "screen", "시스템 화면 + 단계", "image(캡처, 선택) · steps"),
       (14, "case", "사례 카드", "tag · heading · lines · illust"),
       (15, "emphasis", "크게 보여 줄 한 문장", "statement · sub · illust"),
       (16, "quiz · ox", "O / X 퀴즈", "question · type: ox"),
       (18, "quiz · choice", "2–4지 선택 퀴즈", "question · options"),
       (17, "answer", "정답 + 해설", "answer · headline · explain"),
       (20, "summary", "핵심 정리 체크", "items · illust"),
       (21, "ending", "마무리 · 다음 차시", "title · sub · illust")]
for pi in range(3):
    chunk = cat[pi * 6:(pi + 1) * 6]
    cs = "".join(f'<div class="lc"><div class="frame sm">{slide_svg(n, 344)}</div><div class="lc-t"><b>{nm}</b><span>{d}</span></div><code>{f}</code></div>' for n, nm, d, f in chunk)
    P.append(page(f"07 · 레이아웃 {pi + 1}/3", "레이아웃 17종 — 견본 덱 ‘개인정보보호 기본 교육’", f'<div class="lcg">{cs}</div>', 9 + pi, cls="tight"))

# 12 workflow
yaml_snip = html.escape("""- layout: concept
  label: 1-1. 개인정보 정의
  title: 개인정보란?
  lines: [사망자의 정보라도, 유족과의 관계를 알 수 있는 정보는]
  emphasis: 유족의 개인정보에 해당
  illust: question
  key: 고인 정보도 함부로 공개하면 안 됩니다
  say: 사망자의 정보라도 유족과의 관계를 알 수 있다면 …""")
P.append(page("08 · 사용 방법", "원고를 넣으면 바로 PPT로", f'''<div class="row">
<div class="steps3">
  <div class="st"><span>1</span><div><b>원고를 붙여 넣고 요청</b><p>"이 원고로 교육 영상 PPT 만들어줘" (/edu-video). 텍스트·워드·PDF·기존 PPT 모두 됩니다.</p></div></div>
  <div class="st"><span>2</span><div><b>Claude가 화면을 나누고 YAML로 정리</b><p>한 화면 한 메시지로 나눠 레이아웃·일러스트·핵심 한 줄·강의 원고(노트)를 정합니다.</p></div></div>
  <div class="st"><span>3</span><div><b>자동 빌드 · 검사 · 납품</b><p>넘침·강사 영역 침범·21pt 미만 글자를 검사하고 렌더를 확인한 뒤 편집 가능한 PPTX를 전달합니다.</p></div></div>
</div>
<div class="side"><h3 class="h3">한 화면 = YAML 한 블록</h3><pre>{yaml_snip}</pre>
<p class="small">형식 전체: references/content-format.md · 견본: examples/privacy_basics.yaml</p></div></div>''', 12))

# 13 editing guide + do/don't
do = ["한 화면에 한 메시지, 항목 4개 이하", "핵심 문구를 강사가 말로도 읽기", "일러스트는 주제에 맞는 것 하나만", "시스템 캡처는 screen 레이아웃 프레임 안에"]
dont = ["강사 영역·자막 영역에 글자나 그림 넣기", "21pt보다 작은 글자, 얇은 서체", "색깔만으로 정답·강조 표시", "스톡 사진·클립아트·이모지·그라디언트"]
P.append(page("09 · 영상 편집 가이드", "합성할 때 지킬 것", f'''<div class="row">
<div><table class="t"><tr><th>항목</th><th>기준 (1080p)</th></tr>
<tr><td>내보내기</td><td>PowerPoint → 내보내기 → PNG 1920×1080</td></tr>
<tr><td>강사 배치</td><td>크로마키 후 x 1344–1920, 허리선 위 구도</td></tr>
<tr><td>손짓 한계</td><td>x 1308 왼쪽(콘텐츠)으로 넘어오지 않게</td></tr>
<tr><td>자막</td><td>y 966–1080 띠 안, 가운데 정렬</td></tr>
<tr><td>강사 영역 배경</td><td>tint(연한 네이비) 기본 · 하늘색 의상이면 plain</td></tr>
<tr><td>전환</td><td>컷 또는 0.3초 이하 페이드, 깜빡임 금지</td></tr></table></div>
<div class="side dd"><div class="do"><h3>DO</h3><ul>{''.join(f'<li>{x}</li>' for x in do)}</ul></div>
<div class="dont"><h3>DON'T</h3><ul>{''.join(f'<li>{x}</li>' for x in dont)}</ul></div></div></div>''', 13))

FONT = (ROOT / "fonts" / "PretendardVariable.woff2").as_uri()
CSS = f"""
@font-face {{ font-family: Pretendard; src: url('{FONT}') format('woff2'); font-weight: 100 900; }}
@page {{ size: 1280px 720px; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; color: #1A1A1A; background: #FFFFFF; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.pg {{ width: 1280px; height: 720px; padding: 52px 64px 0; position: relative; overflow: hidden; page-break-after: always; display: flex; flex-direction: column; }}
.pg header {{ display: flex; flex-direction: column; gap: 10px; margin-bottom: 26px; }}
.lab {{ align-self: flex-start; background: #E0EDF3; color: #012281; font-weight: 700; font-size: 16px; padding: 6px 16px; border-radius: 999px; }}
.pg h1 {{ font-size: 34px; font-weight: 800; letter-spacing: -0.6px; padding-bottom: 16px; border-bottom: 2px solid #DFDFDF; position: relative; }}
.pg h1::after {{ content: ''; position: absolute; left: 0; bottom: -3px; width: 88px; height: 4px; background: #012281; }}
.pg .body {{ flex: 1; }}
.pg footer {{ position: absolute; left: 64px; right: 64px; bottom: 22px; display: flex; justify-content: space-between; font-size: 13px; color: #666666; }}
.tight {{ padding-top: 40px; }}
.tight header {{ margin-bottom: 16px; }}
.cover {{ background: #012281; color: #FFFFFF; flex-direction: row; align-items: center; gap: 40px; padding: 0 56px 0 72px; }}
.cv-l {{ flex: 1; display: flex; flex-direction: column; gap: 18px; }}
.logo {{ width: 190px; margin-bottom: 30px; }}
.eyebrow {{ align-self: flex-start; color: #58CCFF; border: 2px solid #58CCFF; border-radius: 999px; padding: 6px 18px; font-weight: 700; font-size: 17px; letter-spacing: 1px; }}
.cover h1 {{ font-size: 60px; line-height: 1.15; font-weight: 800; letter-spacing: -1.5px; border: 0; padding: 0; }}
.cover h1::after {{ display: none; }}
.cover p {{ color: #D2D6E3; font-size: 19px; line-height: 1.6; }}
.cover p b {{ color: #58CCFF; }}
.date {{ color: #D2D6E3; font-size: 16px; margin-top: 18px; }}
.cv-r {{ display: flex; flex-direction: column; gap: 12px; }}
.frame {{ border-radius: 14px; overflow: hidden; box-shadow: 0 0 0 1px #DFDFDF; line-height: 0; background: #FFFFFF; }}
.cover .frame {{ box-shadow: none; }}
.cap {{ color: #D2D6E3; font-size: 15px; text-align: center; }}
.grid4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }}
.pc {{ background: #F8F8F8; border-radius: 20px; padding: 28px 24px; display: flex; flex-direction: column; gap: 14px; min-height: 360px; }}
.pc-n {{ width: 52px; height: 52px; border-radius: 16px; background: #012281; color: #fff; font-weight: 800; font-size: 20px; display: flex; align-items: center; justify-content: center; }}
.pc h3 {{ font-size: 24px; font-weight: 800; color: #012281; }}
.pc p {{ font-size: 17px; line-height: 1.65; flex: 1; }}
.tag {{ align-self: flex-start; background: #E0EDF3; color: #012281; font-weight: 700; font-size: 15px; padding: 6px 12px; border-radius: 8px; }}
.note {{ margin-top: 22px; background: #E0EDF3; color: #012281; border-radius: 14px; padding: 16px 22px; font-size: 16px; font-weight: 600; line-height: 1.6; }}
.row {{ display: flex; gap: 36px; align-items: flex-start; }}
.side {{ flex: 1; display: flex; flex-direction: column; gap: 14px; }}
.t {{ border-collapse: collapse; width: 100%; font-size: 16px; }}
.t th {{ text-align: left; background: #012281; color: #fff; font-weight: 700; padding: 10px 14px; }}
.t td {{ padding: 10px 14px; border-bottom: 1px solid #DFDFDF; vertical-align: middle; line-height: 1.5; }}
.nw td:nth-child(n+2) {{ white-space: nowrap; }}
.t .tk {{ font-weight: 800; color: #012281; white-space: nowrap; }}
.ty td {{ padding: 6px 14px; }}
.acc td {{ font-size: 17px; padding: 11px 14px; }}
.muted {{ color: #595959; }}
.small {{ font-size: 15px; color: #595959; line-height: 1.6; }}
code, pre {{ font-family: 'D2Coding', Consolas, monospace; }}
code {{ background: #F8F8F8; padding: 2px 6px; border-radius: 4px; font-size: 14px; }}
.sws {{ display: grid; grid-template-columns: repeat(8, 1fr); gap: 14px; }}
.sw {{ display: flex; flex-direction: column; gap: 6px; font-size: 14px; }}
.sw .chip {{ height: 86px; border-radius: 14px; }}
.sw b {{ font-size: 15px; }}
.sw span {{ color: #595959; line-height: 1.45; }}
.h3 {{ font-size: 19px; font-weight: 800; color: #012281; margin: 22px 0 12px; }}
.side .h3 {{ margin-top: 0; }}
.cps {{ display: grid; grid-template-columns: repeat(9, 1fr); gap: 10px; }}
.cp {{ border-radius: 12px; padding: 14px 10px; display: flex; flex-direction: column; align-items: center; gap: 6px; }}
.cp b {{ font-size: 22px; }}
.cp span {{ font-size: 14px; font-weight: 700; }}
.ilg {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 18px 6px; }}
.il {{ display: flex; flex-direction: column; align-items: center; text-align: center; gap: 2px; }}
.il svg {{ width: 108px; height: 108px; }}
.il b {{ font-size: 14px; color: #012281; }}
.il span {{ font-size: 12.5px; color: #595959; line-height: 1.35; }}
.rep {{ flex: 1.5; }}
.rep td {{ padding: 8px 12px; }}
.rep .arrow {{ font-size: 26px; color: #012281; font-weight: 800; }}
.rep .ic {{ width: 110px; line-height: 0; }}
.ul {{ list-style: none; display: flex; flex-direction: column; gap: 8px; font-size: 16px; }}
.ul li::before {{ content: '· '; color: #012281; font-weight: 800; }}
.dks {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 6px; }}
.dk {{ background: #012281; border-radius: 14px; display: flex; justify-content: center; padding: 6px; line-height: 0; }}
.lcg {{ display: grid; grid-template-columns: repeat(3, 344px); justify-content: space-between; gap: 10px 0; }}
.lc {{ display: flex; flex-direction: column; gap: 4px; }}
.lc-t {{ display: flex; gap: 10px; align-items: baseline; margin-top: 4px; }}
.lc-t b {{ font-size: 17px; color: #012281; font-weight: 800; }}
.lc-t span {{ font-size: 15px; }}
.lc code {{ align-self: flex-start; font-size: 12.5px; color: #595959; }}
.steps3 {{ flex: 1; display: flex; flex-direction: column; gap: 18px; }}
.st {{ display: flex; gap: 18px; background: #F8F8F8; border-radius: 18px; padding: 22px 24px; }}
.st > span {{ flex: none; width: 48px; height: 48px; border-radius: 50%; background: #012281; color: #fff; font-weight: 800; font-size: 22px; display: flex; align-items: center; justify-content: center; }}
.st b {{ font-size: 20px; }}
.st p {{ font-size: 16px; line-height: 1.6; margin-top: 6px; color: #1A1A1A; }}
pre {{ background: #0B1A4A; color: #E0EDF3; border-radius: 14px; padding: 18px 20px; font-size: 14.5px; line-height: 1.6; white-space: pre-wrap; }}
.dd {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
.do, .dont {{ border-radius: 18px; padding: 20px 22px; }}
.do {{ background: #E0EDF3; }} .dont {{ background: #F8F8F8; border: 2px solid #DFDFDF; }}
.do h3 {{ color: #012281; font-size: 20px; margin-bottom: 10px; }} .dont h3 {{ color: #595959; font-size: 20px; margin-bottom: 10px; }}
.do li, .dont li {{ font-size: 16px; line-height: 1.55; margin: 0 0 8px 18px; }}
"""

OUTD.mkdir(parents=True, exist_ok=True)
H = OUTD / "design-system.html"
H.write_text(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>교육 영상 배경 PPT 디자인 시스템</title><style>{CSS}</style></head>'
             f'<body>{"".join(P)}</body></html>', encoding="utf-8")
print("html:", H)

js = OUTD / "print.js"
js.write_text("""const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await p.goto(process.argv[2], { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: process.argv[3], width: '1280px', height: '720px', printBackground: true, preferCSSPageSize: true });
  if (process.argv[4]) { await p.setViewportSize({ width: 1280, height: 720 });
    const n = await p.$$eval('section.pg', s => s.length);
    for (let i = 0; i < n; i++) { const el = (await p.$$('section.pg'))[i]; await el.screenshot({ path: `${process.argv[4]}/p${String(i + 1).padStart(2, '0')}.png` }); } }
  await b.close();
})();
""", encoding="utf-8")
node = shutil.which("node")
if not node:
    sys.exit("node not found — open the HTML in Chrome and print to PDF (1280×720px, no margins, background graphics on)")
shots = OUTD / "png"
shots.mkdir(exist_ok=True)
r = subprocess.run([node, str(js), H.as_uri(), str(PDF), str(shots)], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("playwright print failed:\n" + r.stderr[-1500:] + "\n→ open the HTML in Chrome and print to PDF instead")
print("pdf:", PDF, f"({PDF.stat().st_size // 1024} KB) · page PNGs:", shots)
