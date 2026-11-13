#!/usr/bin/env python3
"""build_deck.py — content YAML → edu-video SVG pages (+ plan, notes, spec) in output/<project>/.

Usage (repo root):
    .claude/skills/slide/scripts/_py.sh .claude/skills/edu-video/scripts/build_deck.py <content.yaml> [--project NAME]

Then the three post-processing calls (each a separate bash call) and finish.py — the script prints them.
Content format: .claude/skills/edu-video/references/content-format.md
Exit 1 with a per-slide list when any slide does not fit the design system (nothing is silently cut).
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE / "evkit"))
sys.path.insert(0, str(ROOT / ".claude/skills/generic-redesign/scripts/ilkit"))

import yaml  # noqa: E402

import ev  # noqa: E402
import evcheck  # noqa: E402
import kit  # noqa: E402  (project bootstrap: init + plan helpers)
from planlib import slide as plan_slide, write_plan  # noqa: E402

ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
GM_BAND = (ev.KEY_Y, ev.KEY_Y + ev.KEY_H)   # verify_deck reads <project>/.gm_band


SKIP_KEYS = {"layout", "illust", "icon", "type", "highlight", "current", "mark", "number", "image", "minutes", "say", "_auto_no", False}


def screen_text(s):
    """All on-screen text in reading order — goes into the notes so the instructor can read the
    screen aloud for learners who cannot see it (design-system.md A7)."""
    out = []

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k not in SKIP_KEYS:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif v is not None and str(v).strip():
            out.append(str(v).replace("**", "").replace(" | ", " "))
    order = ["label", "title", "eyebrow", "lead", "caption", "value", "unit", "statement", "source", "text", "lines",
             "emphasis", "question", "headline", "answer", "explain", "items", "left", "right", "steps", "options",
             "desc", "sub", "meta", "tag", "heading", "cite", "key"]
    for k in order + [k for k in s if k not in order]:
        if k in s and k not in SKIP_KEYS:
            walk(s[k] if k != "cite" else f"출처 {s[k]}")
    return " / ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("--project")
    a = ap.parse_args()
    try:
        doc = yaml.safe_load(open(a.content, encoding="utf-8"))
    except yaml.YAMLError as e:
        sys.exit(f"YAML error — usually an unquoted comma or colon inside {{…}} / […]; quote that value.\n{e}")
    proj = a.project or doc.get("project")
    if not proj:
        sys.exit("set `project:` in the YAML or pass --project")
    slides = doc.get("slides") or []
    if not slides:
        sys.exit("no slides in the YAML")

    ev.STAGE = doc.get("stage", "tint")
    ev.LOGO = bool(doc.get("logo", True))
    ev.ICON_DIR = str(ROOT / "assets/icons/tabler-outline")

    images = []
    src_dir = Path(a.content).resolve().parent
    for s in slides:
        if s.get("image"):
            p = Path(s["image"])
            p = p if p.is_absolute() else src_dir / p
            if not p.exists():
                sys.exit(f"image not found: {p}")
            images.append((str(p), p.name))
            s["image"] = p.name

    P = Path(kit.init(proj, images))
    ev.OUT = str(P / "svg_output")
    for f in glob.glob(os.path.join(ev.OUT, "*.svg")):
        os.remove(f)

    errors, names = [], []
    chap = 0
    for i, s in enumerate(slides, 1):
        if s.get("layout") == "chapter":
            chap += 1
            s["_auto_no"] = chap
        for k, v in s.items():                      # flow lists split on commas: [a, b, c]
            if isinstance(v, list) and any(isinstance(x, str) and len(x.strip()) <= 1 for x in v):
                errors.append(f"slide {i}: `{k}` has a 1-character item {v!r} — an unquoted comma split the list; "
                              f"quote the item or use a block list (- …)")
        if False in s:
            errors.append(f"slide {i}: key `no:` is read as false by YAML — use `number:`")
    for i, s in enumerate(slides, 1):
        try:
            names.append(ev.build_page(i, s))
        except (ev.FitError, KeyError, TypeError) as e:
            errors.append(f"slide {i} ({s.get('layout')}): {e}")
            names.append(None)
    for n in filter(None, names):
        errors += evcheck.check_svg(open(os.path.join(ev.OUT, n), encoding="utf-8").read(), n)
    if errors:
        print("FIT ERRORS — fix the content (shorten, split, or change layout) and rebuild:")
        print("\n".join("  " + e for e in errors))
        sys.exit(1)

    # .gm_band: the key strip sits above the caption safe zone, not at the default y 655–705
    (P / ".gm_band").write_text(f"{GM_BAND[0]} {GM_BAND[1]}\n", encoding="utf-8")

    # notes = narration script (say:) — one per slide, stems match SVG names
    with open(P / "notes" / "total.md", "w", encoding="utf-8") as f:
        for n, s in zip(names, slides):
            screen = screen_text(s)
            say = (s.get("say") or "").strip()
            body = (say + "\n\n" if say else "") + "[화면 읽기] " + screen
            f.write(f"# {n[:-4]}\n\n{('[전환] ' if n[:2] != '01' else '') + body}\n\n소요 시간: {s.get('minutes', 1)}분\n\n")

    # slide_plan.json (deck_type educational) — validated by verify_deck
    t0 = slides[0].get("title", proj)
    title = doc.get("title") or (" ".join(t0) if isinstance(t0, list) else t0)
    plan = []
    for i, s in enumerate(slides, 1):
        fn, shell, role, fam, pg, blk = ev.LAYOUTS[s["layout"]]
        ti = " ".join(s["title"]) if isinstance(s.get("title"), list) else (s.get("title") or s.get("statement") or s["layout"])
        core = s.get("key") or ti
        plan.append(plan_slide(i, role, fam, ti, core, core,
                               f"{s['layout']} 레이아웃 — 강의 흐름상 {i}번째, 앞 장의 설명을 이어받는다",
                               [(blk, ti, core)], page=pg))
    write_plan(str(P / "slide_plan.json"),
               {"working_title": title, "deck_goal": doc.get("goal", "교육 영상 배경 슬라이드"), "deck_type": "educational",
                "target_audience": doc.get("audience", "온라인 교육 영상 학습자 (저시력 학습자 포함)"), "tone": "친절한 해요체/합니다체",
                "target_length": {"slides": len(slides), "reasoning": "강의 원고 흐름 1:1 (한 화면 한 메시지)"}},
               {"narrative_shape": "도입 → 개념 → 예시 → 확인 → 정리",
                "why_this_order_is_persuasive": "개념을 먼저 세우고 사례와 퀴즈로 확인한 뒤 요약해 기억에 남긴다"},
               [{"source_id": "src_01", "source_type": "file", "summary": os.path.basename(a.content), "relevance": "high", "usable_for": ["all"]}],
               plan,
               fact=[{"claim": "강의 원고 내용", "slide_number": 1, "priority": "MEDIUM", "status": "unverified", "source": None,
                      "original": "사용자 제공 원고 — 법령·수치는 사용자 확인 필요", "corrected_to": None, "checked_at": date.today().isoformat()}])
    res = subprocess.run([kit.PY, str(ROOT / ".claude/skills/slide-plan/scripts/validate_plan.py"), str(P / "slide_plan.json")],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    out = [l for l in (res.stdout + res.stderr).splitlines() if "ERROR" in l or "violation" in l or "OK" in l or "FAIL" in l]
    print("plan:", "; ".join(out) or res.returncode)
    if res.returncode != 0:
        print("slide_plan.json failed validation — usually R4 (3+ consecutive slides of one layout family): vary the layouts")
        sys.exit(1)

    (P / "design_spec.md").write_text(
        f"# {proj} - Design Spec\n\n> edu-video design system (.claude/skills/edu-video/references/design-system.md). "
        f"Active theme: Insightlearning.\n\n| Item | Value |\n| --- | --- |\n| Canvas | 1280×720 |\n| Pages | {len(slides)} |\n"
        f"| Content zone | x 64–848 (left 70%) |\n| Instructor stage | x 896–1280 ({ev.STAGE}) |\n| Caption safe zone | y 644–720 |\n"
        f"| Type | min 28px · body 32px · title 44px · display 64px |\n", encoding="utf-8")
    kit.checkall(proj)
    print(f"\nOK — {len(slides)} pages in output/{proj}/svg_output. Next (each a separate call):")
    rel = f"output/{proj}"
    for c in (f".claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/total_md_split.py {rel}",
              f".claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/finalize_svg.py {rel}",
              f".claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/svg_to_pptx.py {rel} -s final",
              f".claude/skills/slide/scripts/_py.sh .claude/skills/edu-video/scripts/finish.py {proj} \"{doc.get('deliver', proj + '.pptx')}\""):
        print("  " + c)


if __name__ == "__main__":
    main()
