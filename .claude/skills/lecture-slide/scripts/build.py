#!/usr/bin/env python3
"""build.py — deck.yaml(또는 .json) → output/<project>/svg_output/*.svg + notes + plan.

Usage:
    _py.sh .claude/skills/lecture-slide/scripts/build.py <deck.yaml> [--project NAME]

그다음 후처리 3단계(각각 별도 호출) → finish.py. 형식은 references/deck-format.md.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import lskit as K  # noqa: E402

SK = ROOT / ".claude" / "skills"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

ROLE = {"cover": "cover", "toc": "agenda", "chapter": "context", "ending": "cta", "quiz": "exercise",
        "statement": "concept", "keywords": "concept", "bullets": "summary", "stats": "evidence",
        "chart": "evidence", "table": "evidence", "text_image": "example", "image_grid": "example",
        "two_col": "concept", "before_after": "insight", "cause_result": "insight", "cards": "concept",
        "points": "concept", "process": "concept", "steps": "concept", "timeline": "concept"}
BLOCK = {"stats": "metric_cards", "chart": "chart", "table": "table", "process": "diagram_flow",
         "steps": "diagram_flow", "timeline": "diagram_flow", "cards": "icon_group", "points": "icon_group",
         "text_image": "image", "image_grid": "image", "two_col": "image", "keywords": "infographic",
         "before_after": "infographic", "cause_result": "infographic", "statement": "callout",
         "quiz": "callout", "bullets": "bullets", "toc": "bullets"}
FAMILY_SHELL = {"cover": "visual", "chapter": "structure", "ending": "insight"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def load(path: Path) -> dict:
    txt = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(txt)
    import yaml
    return yaml.safe_load(txt)


def init_project(P: Path, name: str):
    if not (P / "templates").is_dir():
        subprocess.run([sys.executable, str(SK / "slide" / "scripts" / "project_manager.py"), "init", name,
                        "--format", "ppt169"], cwd=ROOT, capture_output=True, env=ENV)
    for d in ("templates", "images", "svg_output", "svg_final", "notes", "exports", "sources"):
        (P / d).mkdir(parents=True, exist_ok=True)
    for f in (P / "svg_output").glob("*.svg"):        # rebuild from scratch (deleted slides must disappear)
        f.unlink()


def stage_image(v, base: Path, P: Path):
    """deck의 이미지 경로 → images/<파일명>. 없거나 빈 값이면 None (플레이스홀더)."""
    if not v:
        return None
    src = Path(v)
    if not src.is_absolute():
        src = (base / src).resolve()
    if not src.is_file() or src.suffix.lower() not in IMG_EXT:
        K.WARN.append(f"image not found or unsupported: {v} → placeholder")
        return None
    dst = P / "images" / src.name
    if src != dst:
        shutil.copy(src, dst)
    return src.name


def stage_images(s: dict, base: Path, P: Path):
    if "image" in s:
        s["image"] = stage_image(s["image"], base, P)
    if "images" in s:
        s["images"] = [stage_image(v, base, P) for v in s["images"]]
    for c in s.get("cols", []) or []:
        if isinstance(c, dict) and "image" in c:
            c["image"] = stage_image(c["image"], base, P)


CONTENT_KEYS = {"layout", "eyebrow", "title", "gm", "lead", "notes"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("--project")
    a = ap.parse_args()
    deck_path = Path(a.deck).resolve()
    D = load(deck_path)
    name = a.project or D.get("project") or deck_path.stem
    P = ROOT / "output" / name
    init_project(P, name)
    K.OUT = str(P / "svg_output")

    brand = D.get("brand", "")
    tl, tr = D.get("top_left", ""), D.get("top_right", "")
    slides = D["slides"]
    missing = [f"#{i} ({s.get('layout')})" for i, s in enumerate(slides, 1)
               if s.get("layout") not in K.SHELLS and not s.get("gm")]
    if missing:
        sys.exit("gm (governing message) missing on content slides: " + ", ".join(missing))

    notes, plan_rows = [], []
    section = ""
    errors = []
    for i, s in enumerate(slides, 1):
        s = dict(s)
        lay = s.get("layout")
        stage_images(s, deck_path.parent, P)
        stem = f"{i:02d}_{lay}"
        fname = stem + ".svg"
        K.begin(fname)
        try:
            if lay == "cover":
                K.cover(fname, s["title"], s.get("subtitle"), s.get("badge"), s.get("info", ()),
                        s.get("top_left", tl), s.get("top_right", tr), s.get("brand", brand))
            elif lay == "chapter":
                section = s.get("eyebrow") or s.get("label") or ""
                K.chapter(fname, s["title"], s.get("label", "CHAPTER"), s.get("sub"),
                          s.get("top_left", tl), s.get("top_right", tr), s.get("brand", brand))
            elif lay == "ending":
                K.ending(fname, s.get("title", "감사합니다"), s.get("subtitle"), s.get("badge", "THANK YOU"),
                         s.get("contacts", ()), s.get("top_left", tl), s.get("top_right", tr), s.get("brand", brand))
            elif lay in K.LAYOUTS:
                fn, _ = K.LAYOUTS[lay]
                lead = s.get("lead")
                top = K.TOP_LEAD if lead else K.TOP
                fields = {k: v for k, v in s.items() if k not in CONTENT_KEYS}
                body = fn(top, K.BOTTOM, **fields)
                K.content_page(fname, s.get("eyebrow") or section or (D.get("title") or ""), s["title"],
                               s["gm"], i, body, lead, s.get("footer", D.get("footer", brand)))
            else:
                errors.append(f"#{i}: unknown layout '{lay}' (use one of {', '.join(list(K.LAYOUTS) + list(K.SHELLS))})")
                continue
        except K.SafeZoneError as e:
            errors.append(str(e))
            continue
        except TypeError as e:
            errors.append(f"#{i} {lay}: bad field — {e}")
            continue
        title = s.get("title", "")
        notes.append((stem, (s.get("notes") or f"{title}. {s.get('gm', '')}").strip()))
        plan_rows.append((i, lay, title, s.get("gm") or title))

    for w in K.WARN:
        print("[WARN]", w)
    if errors:
        for e in errors:
            print("[ERROR]", e)
        sys.exit(f"{len(errors)} slide(s) failed — fix deck and rebuild")

    (P / "notes" / "total.md").write_text(
        "\n".join(f"# {k}\n\n{('[전환] ' if n > 0 else '') + v}\n" for n, (k, v) in enumerate(notes)),
        encoding="utf-8")
    (P / ".theme-color-allow").write_text("\n".join(K.PALETTE) + "\n", encoding="utf-8")
    write_plan(P, D, plan_rows)
    write_spec(P, D, plan_rows)
    print(f"built {len(notes)} slides → {P / 'svg_output'}")


def write_plan(P: Path, D: dict, rows):
    slides = []
    for n, lay, title, core in rows:
        fam = FAMILY_SHELL.get(lay) or K.LAYOUTS[lay][1]
        page = {"cover": "title", "chapter": "chapter", "ending": "end"}.get(lay, "body")
        blk = BLOCK.get(lay, "title")
        slides.append({
            "slide_number": n, "slide_role": ROLE.get(lay, "concept"), "page_family": page,
            "working_title": title or lay, "core_message": core, "audience_takeaway": core,
            "why_here": f"강의 흐름상 {n}번째 — 앞 장을 이어받아 '{title or lay}'을(를) {lay} 레이아웃으로 설명한다",
            "recommended_layout_family": fam,
            "content_blocks": [{"block_type": blk, "purpose": title or lay, "content_instruction": core}],
            "chart_strategy": "focus-comparison" if lay == "chart" else None,
            "chart_takeaway": core if lay == "chart" else None,
            "table_strategy": "table" if lay == "table" else None, "table_takeaway": core if lay == "table" else None,
            "content_constraints": {"must_include": [], "must_not_include": [], "evidence_to_use": ["src_01"]},
            "evidence_sources": ["src_01"], "priority": "must",
        })
    plan = {
        "deck_meta": {"working_title": D.get("title", P.name), "deck_goal": D.get("goal", "강의 영상 배경 슬라이드"),
                      "deck_type": "educational", "target_audience": D.get("audience", "온라인 강의 수강생"),
                      "tone": "lecture, 합니다체", "target_length": {"slides": len(rows), "reasoning": "사용자 제공 강의 원고 기준"}},
        "design_dependency": {"preset_name": "lecture-video",
                              "design_md_path": ".claude/skills/lecture-slide/DESIGN.md",
                              "allowed_layout_families": ["structure", "insight", "breakdown", "compare", "data", "process", "visual"],
                              "consistency_notes": ["오른쪽 30% 강사 영역 비움 (x ≥ 896)", "콘텐츠 존 x 56–856 중심 정렬"]},
        "story_arc": {"narrative_shape": "lecture", "why_this_order_is_persuasive": "강의 원고 순서를 그대로 따른다"},
        "content_inventory": [{"source_id": "src_01", "source_type": "user", "summary": "사용자 제공 강의 내용",
                               "relevance": "high", "usable_for": ["all"]}],
        "slides": slides,
        "ordering_notes": {"split_topics": [], "merged_topics": [], "deferred_topics": [], "appendix_candidates": []},
        "fact_check_log": [{"claim": "강의 내용 (사용자 제공)", "slide_number": 1, "priority": "LOW", "status": "unverified",
                            "source": None, "original": "사용자 원고", "corrected_to": None, "checked_at": date.today().isoformat()}],
    }
    (P / "slide_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    res = subprocess.run([sys.executable, str(SK / "slide-plan" / "scripts" / "validate_plan.py"), str(P / "slide_plan.json")],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if res.returncode:
        print(res.stdout[-1500:], res.stderr[-800:])
        sys.exit("slide_plan.json failed validation")


def write_spec(P: Path, D: dict, rows):
    out = [f"# {D.get('title', P.name)} - Design Spec\n",
           "> Lecture Video theme (`.claude/skills/lecture-slide/DESIGN.md`). 1280×720 · 오른쪽 30% 강사 영역 비움.\n",
           "| # | layout | title | GM |", "|---|---|---|---|"]
    out += [f"| {n} | {lay} | {ti} | {gm} |" for n, lay, ti, gm in rows]
    (P / "design_spec.md").write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
