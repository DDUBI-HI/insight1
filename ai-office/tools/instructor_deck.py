#!/usr/bin/env python3
"""강사풀 PPT(예: MindAILab AI/AX 전문강사풀)에 새 강사 장을 '같은 규격·디자인'으로 추가한다.

원본은 읽기만 하고, 결과는 항상 새 파일로 쓴다(같은 이름이 있으면 거부).

    python instructor_deck.py analyze <deck.pptx>
        → JSON: 강사 장 위치, 칸별 줄 수·글자 수 한도, 예시 2명, 이미 있는 이름, 요약표 정보
    python instructor_deck.py add <deck.pptx> <profile.json> <out.pptx> [--preview <dir>]
        → 기존 강사 장을 복제해 글만 바꾼 새 장을 마지막 강사 뒤에 넣고,
          '강사풀 한눈에 보기' 표에 한 줄 추가(자리가 없으면 표 장을 하나 더),
          '65인·65명' 같은 인원 수와 쪽 번호를 다시 맞춘다. 결과 JSON 출력.

profile.json 형식(analyze 의 fields 한도를 지킨다):
    {"name": "", "affiliation": [], "specialties": [], "education_label": "학력 · 자격", "education": [], "strength_title": "",
     "strength_body": "", "references": [], "programs": []}

python-pptx 만 쓴다(slide-svg 가상환경에 있음). 출력은 UTF-8 JSON.
"""
from __future__ import annotations

import copy
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.oxml.ns import qn

# 강사 장을 알아보는 꼬리표(칸 이름) → 그 뒤에 오는 글 상자들이 어떤 칸인지
LABELS = [
    (r"AI INSTRUCTOR", ["name", "affiliation"]),
    (r"^전문 분야$", ["specialties"]),
    (r"^(학력|경력|자격|활동)\s*·", ["education"]),   # 칸 이름이 강사마다 다르다: 학력 · 자격 / 경력 · 활동 …
    (r"^STRENGTH", ["strength_title", "strength_body"]),
    (r"^REFERENCE", ["references_left", "references_right"]),
    (r"^PROGRAM", ["programs"]),
]
EDU_LABELS = ("학력 · 자격", "경력 · 학력", "경력 · 자격", "경력 · 활동")
LIST_FIELDS = ("affiliation", "specialties", "education", "programs")
COUNT_RE = re.compile(r"(?<![\d,])(\d{1,3})(?=\s*(인|명))")
PAGE_RE = re.compile(r"^\d{1,3}$")
FRACTION_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s*$")


def out(obj, code=0):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(obj, ensure_ascii=False, indent=1))
    sys.exit(code)


def text_shapes(slide):
    return [s for s in slide.shapes if s.has_text_frame]


def lines_of(shape):
    return [p.text for p in shape.text_frame.paragraphs if p.text.strip()]


def field_map(slide):
    """강사 장이면 {칸: 도형 이름}, 아니면 None"""
    shapes = text_shapes(slide)
    texts = [s.text_frame.text.strip() for s in shapes]
    m = {}
    for lab, fields in LABELS:
        i = next((k for k, t in enumerate(texts) if len(t) < 60 and re.search(lab, t)), None)
        if i is None:
            return None
        nxt = [s for s in shapes[i + 1:i + 1 + len(fields)]]
        if len(nxt) < len(fields):
            return None
        for f, s in zip(fields, nxt):
            m[f] = s.name
        if fields == ["education"]:
            m["education_label"] = shapes[i].name
    return m


def table_of(slide):
    for s in slide.shapes:
        if s.has_table:
            return s
    return None


def by_name(slide, name):
    for s in slide.shapes:
        if s.name == name:
            return s
    return None


def analyze(prs):
    slides = list(prs.slides)
    profiles = [(i, field_map(s)) for i, s in enumerate(slides)]
    profiles = [(i, m) for i, m in profiles if m]
    if not profiles:
        raise SystemExit("강사 장(전문 분야·STRENGTH·REFERENCE·PROGRAM 칸)을 찾지 못했습니다")
    fmap = profiles[0][1]
    limits = {}
    for f, shape_name in fmap.items():
        if f == "education_label":
            continue
        ls, cs = [], []
        for i, m in profiles:
            sh = by_name(slides[i], m[f])
            ln = lines_of(sh) if sh else []
            ls.append(len(ln))
            cs.extend(len(x) for x in ln)
        cs.sort()
        p75 = cs[int(len(cs) * 0.75)] if cs else 10
        limits[f] = {"max_lines": max(ls) or 1, "max_chars": max(cs or [10]), "target_chars": p75}
    names = [lines_of(by_name(slides[i], m["name"]))[0] for i, m in profiles]

    def profile_json(i, m):
        g = lambda f: lines_of(by_name(slides[i], m[f]))
        return {"name": g("name")[0], "affiliation": g("affiliation"), "specialties": g("specialties"),
                "education_label": g("education_label")[0], "education": g("education"), "strength_title": " ".join(g("strength_title")),
                "strength_body": " ".join(g("strength_body")),
                "references": g("references_left") + g("references_right"), "programs": g("programs")}

    summary = [i for i, s in enumerate(slides) if table_of(s) and i < profiles[0][0]]
    cap = 0
    if summary:
        cap = max(len(table_of(slides[i]).table.rows) for i in summary)
        if len(summary) == 1:
            # 표 장이 하나뿐이면 '가장 긴 표'를 알 수 없다 → 장 아래 여백(0.5인치)까지 들어가는 줄 수로 본다
            ts = table_of(slides[summary[0]])
            rows = ts.table.rows
            row_h = sum(r.height for r in rows) / len(rows) or 1
            fit = int((prs.slide_height - ts.top - 457200) // row_h)
            cap = max(cap, fit)
    col_chars = []
    if summary:
        tbl = table_of(slides[summary[0]]).table
        for c in range(len(tbl.columns)):
            mx = 0
            for i in summary:
                for r in list(table_of(slides[i]).table.rows)[1:]:
                    for p in r.cells[c].text_frame.paragraphs:
                        mx = max(mx, len(p.text))
            col_chars.append(mx)
    return {
        "slides": len(slides),
        "profile_slides": [i + 1 for i, _ in profiles],
        "count": len(profiles),
        "fields": {
            "name": limits["name"], "affiliation": limits["affiliation"], "specialties": limits["specialties"],
            "education": limits["education"], "strength_title": limits["strength_title"],
            "strength_body": {"max_lines": 1, "max_chars": limits["strength_body"]["max_chars"], "target_chars": limits["strength_body"]["target_chars"]},
            "references": {"max_lines": limits["references_left"]["max_lines"] + limits["references_right"]["max_lines"],
                           "max_chars": max(limits["references_left"]["max_chars"], limits["references_right"]["max_chars"]),
                           "target_chars": max(limits["references_left"]["target_chars"], limits["references_right"]["target_chars"])},
            "programs": limits["programs"],
        },
        "education_labels": list(EDU_LABELS),
        "names": names,
        "examples": [profile_json(*profiles[0]), profile_json(*profiles[len(profiles) // 2])],
        "summary_slides": [i + 1 for i in summary],
        "summary_capacity_rows": cap,
        "summary_col_chars": col_chars,
        "_fmap": fmap,
        "_limits": limits,
    }


def check(profile, info):
    """한도 넘침 목록(없으면 빈 목록)"""
    errs = []
    if not str(profile.get("name", "")).strip():
        errs.append("name: 비어 있음")
    for f, lim in info["fields"].items():
        v = profile.get(f, [] if f in LIST_FIELDS + ("references",) else "")
        items = v if isinstance(v, list) else [v]
        items = [str(x) for x in items if str(x).strip()]
        if len(items) > lim["max_lines"]:
            errs.append(f"{f}: {len(items)}줄 → {lim['max_lines']}줄 이하")
        for x in items:
            if len(x) > lim["max_chars"]:
                errs.append(f"{f}: '{x[:20]}…' {len(x)}자 → {lim['max_chars']}자 이하")
    return errs


# ---------- XML 조작 ----------

def set_lines(text_frame, lines):
    """글 상자의 첫 단락·첫 글자 모양을 그대로 두고 글만 바꾼다(단락 수는 lines 에 맞춤)"""
    lines = [str(x) for x in lines if str(x).strip()] or [""]
    txBody = text_frame._txBody
    paras = txBody.findall(qn("a:p"))
    templates = [copy.deepcopy(p) for p in paras] or [txBody.makeelement(qn("a:p"), {})]
    for p in paras:
        txBody.remove(p)
    for i, line in enumerate(lines):
        p = copy.deepcopy(templates[min(i, len(templates) - 1)])
        runs = p.findall(qn("a:r"))
        for extra in runs[1:]:
            p.remove(extra)
        for br in p.findall(qn("a:br")):
            p.remove(br)
        if runs:
            runs[0].find(qn("a:t")).text = line
        else:
            r = p.makeelement(qn("a:r"), {})
            t = r.makeelement(qn("a:t"), {})
            t.text = line
            r.append(t)
            end = p.find(qn("a:endParaRPr"))
            if end is not None:
                end.addprevious(r)
            else:
                p.append(r)
        txBody.append(p)


def duplicate_slide(prs, src_index):
    """src 장을 복제해 맨 끝에 붙이고 그 장을 돌려준다(그림 관계도 복사, 노트는 복사하지 않음)"""
    src = prs.slides[src_index]
    new = prs.slides.add_slide(src.slide_layout)
    for shp in list(new.shapes):
        shp._element.getparent().remove(shp._element)
    rid_map = {}
    for rel in src.part.rels.values():
        if rel.reltype.endswith("/image") or rel.reltype.endswith("/hyperlink"):
            if rel.is_external:
                rid_map[rel.rId] = new.part.relate_to(rel.target_ref, rel.reltype, is_external=True)
            else:
                rid_map[rel.rId] = new.part.relate_to(rel.target_part, rel.reltype)
    tree = new.shapes._spTree
    for el in src.shapes._spTree.iterchildren():
        if el.tag in (qn("p:nvGrpSpPr"), qn("p:grpSpPr")):
            continue
        c = copy.deepcopy(el)
        for node in c.iter():
            for attr in (qn("r:embed"), qn("r:link"), qn("r:id")):
                if node.get(attr) in rid_map:
                    node.set(attr, rid_map[node.get(attr)])
        tree.append(c)
    bg = src._element.cSld.find(qn("p:bg"))
    if bg is not None:
        new._element.cSld.insert(0, copy.deepcopy(bg))
    return new


def move_slide(prs, slide, new_index):
    lst = prs.slides._sldIdLst
    ids = list(lst)
    el = next(x for x in ids if prs.part.related_part(x.rId) is slide.part)
    lst.remove(el)
    lst.insert(new_index, el)


def add_table_row(tbl):
    rows = tbl._tbl.findall(qn("a:tr"))
    new = copy.deepcopy(rows[-1])
    rows[-1].addnext(new)
    return tbl.rows[len(tbl.rows) - 1]


def cut(s, n):
    s = str(s)
    return s if len(s) <= n else s[: max(1, n - 1)] + "…"


def add(deck, profile, out_path, preview_dir=None):
    prs = Presentation(deck)
    info = analyze(prs)
    name = str(profile["name"]).strip()
    if any(re.sub(r"\s", "", n) == re.sub(r"\s", "", name) for n in info["names"]):
        return {"ok": False, "code": "exists", "error": f"'{name}' 강사가 이미 강사풀 PPT 에 있습니다"}
    problems = check(profile, info)
    if problems:
        return {"ok": False, "code": "overflow", "error": "칸 한도를 넘었습니다", "problems": problems}

    fmap = info["_fmap"]
    lim = info["_limits"]
    slides = list(prs.slides)
    old_pos = {s.slide_id: i + 1 for i, s in enumerate(slides)}  # 1부터
    last_profile = info["profile_slides"][-1] - 1
    template = info["profile_slides"][0] - 1   # 서식이 가장 고른 첫 강사 장을 본으로 쓴다

    # 1) 강사 장 추가 — 첫 강사 장을 복제해 마지막 강사 장 뒤에
    new = duplicate_slide(prs, template)
    move_slide(prs, new, last_profile + 1)
    refs = [str(x) for x in profile.get("references", []) if str(x).strip()]
    left_n = min(lim["references_left"]["max_lines"], math.ceil(len(refs) / 2)) if refs else 0
    values = {
        "name": [name], "affiliation": profile.get("affiliation", []), "specialties": profile.get("specialties", []),
        "education": profile.get("education", []), "strength_title": [profile.get("strength_title", "")],
        "education_label": [profile.get("education_label") if profile.get("education_label") in EDU_LABELS else EDU_LABELS[0]],
        "strength_body": [profile.get("strength_body", "")], "references_left": refs[:left_n],
        "references_right": refs[left_n:], "programs": profile.get("programs", []),
    }
    for f, shape_name in fmap.items():
        sh = by_name(new, shape_name)
        set_lines(sh.text_frame, values[f])

    # 2) 요약표 한 줄
    summary_note = ""
    if info["summary_slides"]:
        last_sum = info["summary_slides"][-1] - 1
        tshape = table_of(prs.slides[last_sum])
        target_slide = None
        if len(tshape.table.rows) >= info["summary_capacity_rows"]:
            target_slide = duplicate_slide(prs, last_sum)
            move_slide(prs, target_slide, last_sum + 1)
            t2 = table_of(target_slide).table
            trs = t2._tbl.findall(qn("a:tr"))
            for tr in trs[2:]:
                t2._tbl.remove(tr)
            row = t2.rows[1]
            summary_note = "요약표 장을 하나 더 만들었습니다"
        else:
            row = add_table_row(tshape.table)
        cc = info["summary_col_chars"] or [10, 60, 30, 40]
        cols = [
            [name],
            [cut(" | ".join(values["affiliation"]), cc[1] if len(cc) > 1 else 60)],
            [cut(x, cc[2] if len(cc) > 2 else 30) for x in values["specialties"][:2]],
            [cut(x, cc[3] if len(cc) > 3 else 40) for x in refs[:2]],
        ]
        for c, lines in enumerate(cols[: len(row.cells)]):
            set_lines(row.cells[c].text_frame, lines)
        if target_slide is not None:
            # 'n/7' 표기를 새 장 수에 맞춘다
            sums = [s for s in prs.slides if table_of(s) is not None and list(prs.slides).index(s) < info["profile_slides"][0] + 1]
            total = len(sums)
            for k, s in enumerate(sums, 1):
                for sh in text_shapes(s):
                    for p in sh.text_frame.paragraphs:
                        for r in p.runs:
                            if FRACTION_RE.search(r.text):
                                r.text = FRACTION_RE.sub(f"{k}/{total}", r.text)

    # 3) 인원 수(65인·65명 → 66인·66명)
    old_n, new_n = info["count"], info["count"] + 1
    counted = []
    for idx, s in enumerate(prs.slides, 1):
        if s is new:
            continue
        for sh in text_shapes(s):
            for p in sh.text_frame.paragraphs:
                runs = p.runs
                for j, r in enumerate(runs):
                    t = r.text
                    nt = COUNT_RE.sub(lambda m: str(new_n) if int(m.group(1)) == old_n else m.group(0), t)
                    if nt == t and t.strip() == str(old_n) and j + 1 < len(runs) and runs[j + 1].text.lstrip()[:1] in ("인", "명"):
                        nt = t.replace(str(old_n), str(new_n))
                    if nt == t and t.rstrip().endswith(str(old_n)) and j + 1 < len(runs) and runs[j + 1].text.lstrip()[:1] in ("인", "명"):
                        nt = t[: t.rstrip().rfind(str(old_n))] + str(new_n) + t[len(t.rstrip()):]
                    if nt != t:
                        r.text = nt
                        counted.append(idx)

    # 4) 쪽 번호(오른쪽 위 작은 숫자 상자)
    renum = 0
    for j, s in enumerate(prs.slides, 1):
        k = old_pos.get(s.slide_id)
        if s is new:
            k = template + 1   # 복제본에는 본 장의 쪽 번호가 들어 있다
        if k is None and s.slide_id not in old_pos:
            k = info["summary_slides"][-1]  # 새 요약표 장은 원래 마지막 요약표 장의 번호를 가졌다
        for sh in text_shapes(s):
            t = sh.text_frame.text.strip()
            if PAGE_RE.match(t) and int(t) == k and sh.width < 6 * 914400:
                if t != (f"{j:0{len(t)}d}"):
                    for p in sh.text_frame.paragraphs:
                        for r in p.runs:
                            if r.text.strip():
                                r.text = f"{j:0{len(t)}d}"
                    renum += 1
                break

    out_path = Path(out_path)
    if out_path.exists():
        return {"ok": False, "code": "out_exists", "error": f"결과 파일이 이미 있습니다: {out_path}"}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    new_index = list(prs.slides).index(new) + 1
    res = {"ok": True, "out": str(out_path), "new_slide": new_index, "count": new_n,
           "count_changed_slides": sorted(set(counted)), "renumbered": renum, "summary": summary_note or "요약표에 한 줄 추가"}
    if preview_dir:
        res["preview"] = preview(out_path, [new_index, info["summary_slides"][-1] + (1 if summary_note else 0), 1], preview_dir)
    return res


# ---------- 미리보기(PNG) ----------

def preview(pptx, pages, outdir):
    """PowerPoint(Windows) → 없으면 LibreOffice+pdftoppm/PyMuPDF 로 지정한 장만 PNG. 실패하면 빈 목록"""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    pages = sorted(set(p for p in pages if p))
    made = []
    if os.name == "nt":
        ps = "$ErrorActionPreference='Stop'; $pp=New-Object -ComObject PowerPoint.Application; " \
             f"$d=$pp.Presentations.Open('{str(Path(pptx).resolve())}', $true, $false, $false); " + "".join(
                 f"$d.Slides.Item({n}).Export('{str((outdir / f's{n:02d}.png').resolve())}','PNG',1600,900); " for n in pages) + \
             "$d.Close(); $pp.Quit()"
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, timeout=300, capture_output=True)
            made = [str(outdir / f"s{n:02d}.png") for n in pages if (outdir / f"s{n:02d}.png").exists()]
            if made:
                return made
        except Exception:
            pass
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        for c in (r"C:\Program Files\LibreOffice\program\soffice.exe", r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
            if os.path.exists(c):
                soffice = c
    if not soffice:
        return made
    with tempfile.TemporaryDirectory() as td:
        try:
            subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", td, str(pptx)], check=True, timeout=600, capture_output=True)
        except Exception:
            return made
        pdf = next(Path(td).glob("*.pdf"), None)
        if not pdf:
            return made
        try:
            import fitz  # PyMuPDF (slide-svg 가상환경)
            doc = fitz.open(str(pdf))
            for n in pages:
                if n <= len(doc):
                    f = outdir / f"s{n:02d}.png"
                    doc[n - 1].get_pixmap(dpi=110).save(str(f))
                    made.append(str(f))
            return made
        except ImportError:
            pass
        if shutil.which("pdftoppm"):
            for n in pages:
                base = outdir / f"s{n:02d}"
                subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", str(n), "-l", str(n), "-singlefile", str(pdf), str(base)], capture_output=True)
                if base.with_suffix(".png").exists():
                    made.append(str(base.with_suffix(".png")))
    return made


def main(argv):
    if len(argv) >= 2 and argv[0] == "analyze":
        info = analyze(Presentation(argv[1]))
        info.pop("_fmap"); info.pop("_limits")
        out(info)
    if len(argv) >= 4 and argv[0] == "add":
        prof = json.loads(Path(argv[2]).read_text(encoding="utf-8-sig"))
        prev = argv[argv.index("--preview") + 1] if "--preview" in argv else None
        res = add(argv[1], prof, argv[3], prev)
        out(res, 0 if res.get("ok") else 2)
    out({"ok": False, "error": __doc__}, 1)


if __name__ == "__main__":
    main(sys.argv[1:])
