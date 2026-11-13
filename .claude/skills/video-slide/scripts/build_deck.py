#!/usr/bin/env python3
"""build_deck.py — content spec (YAML/JSON) → output/<project>/svg_output/*.svg + notes/total.md.

Usage:
    build_deck.py <deck.yaml> [--project <slug>]

Then run the three post-processing calls (each separately — root CLAUDE.md) and finish.py:
    .claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/total_md_split.py output/<project>
    .claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/finalize_svg.py output/<project>
    .claude/skills/slide/scripts/_py.sh .claude/skills/slide/scripts/svg_to_pptx.py output/<project> -s final
    .claude/skills/slide/scripts/_py.sh .claude/skills/video-slide/scripts/finish.py <project> "<name>.pptx"

Spec reference: .claude/skills/video-slide/references/layouts.md · sample: examples/sample_deck.yaml
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "vkit"))

import frame      # noqa: E402
import layouts    # noqa: E402
import prim       # noqa: E402
from tokens import BODY_BOTTOM, CARD, GM_BAND, HEADER_Y, PALETTE, PRESENTER_X, SUBTITLE_Y, themed, theme_palette  # noqa: E402

ROOT = HERE.parents[3]
SLIDE = ROOT / ".claude" / "skills" / "slide" / "scripts"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def load(path):
    txt = Path(path).read_text(encoding="utf-8")
    if path.endswith((".yaml", ".yml")):
        import yaml
        return yaml.safe_load(txt)
    return json.loads(txt)


def slug(s):
    s = re.sub(r"[^0-9A-Za-z_-]+", "_", s).strip("_").lower()
    return s or "video_deck"


def init_project(project, lock=False, theme=None):
    P = ROOT / "output" / project
    if not (P / "svg_output").is_dir():
        subprocess.run([sys.executable, str(SLIDE / "project_manager.py"), "init", project, "--format", "ppt169"],
                       cwd=ROOT, capture_output=True, env=ENV)
    for d in ("images", "svg_output", "svg_final", "notes", "exports", "sources", "templates"):
        (P / d).mkdir(parents=True, exist_ok=True)
    for d in ("svg_output", "svg_final"):                     # a rebuild replaces every page
        for f in (P / d).glob("*.svg"):
            f.unlink()
    (P / ".theme-color-allow").write_text("\n".join(theme_palette(theme) + ["#8A9BB8"]) + "\n", encoding="utf-8")
    (P / ".gm-band").write_text(f"{GM_BAND[0]} {GM_BAND[1]}\n", encoding="utf-8")
    (P / ".standalone").write_text("video-slide: content-led deck, no slide_plan.json\n", encoding="utf-8")
    gx = P / ".gm-exempt"
    if lock:
        gx.write_text("video-slide content-lock: the source deck's text may not be extended, so no GM line "
                      "is added (deck spec lock_content: true)\n", encoding="utf-8")
    elif gx.exists():
        gx.unlink()
    return P


# ── zone check: nothing readable in the presenter zone or the subtitle zone ──

TEXT_RE = re.compile(r'<text\b([^>]*)>(.*?)</text>', re.S)


def _attr(a, k, d=None):
    m = re.search(rf'\b{k}="([^"]*)"', a)
    return m.group(1) if m else d


def zone_check(svg, name):
    errs = []
    for m in TEXT_RE.finditer(svg):
        a, inner = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        x, y = float(_attr(a, "x", 0)), float(_attr(a, "y", 0))
        fs, fw = float(_attr(a, "font-size", 16)), int(_attr(a, "font-weight", 400))
        w = prim.measure(inner, fs, fw)
        anc = _attr(a, "text-anchor", "start")
        x0 = x - w / 2 if anc == "middle" else x - w if anc == "end" else x
        x1 = x0 + w
        if y > SUBTITLE_Y and x1 > 176:
            errs.append(f"{name}: text in the subtitle zone (y={y:.0f}): '{inner[:24]}'")
        if x1 > CARD["x"] + CARD["w"] - 12 or x1 > PRESENTER_X:
            errs.append(f"{name}: text runs off the card / into the presenter zone (right edge {x1:.0f}): '{inner[:24]}'")
        if x0 < CARD["x"] + 8:
            errs.append(f"{name}: text starts outside the card (x={x0:.0f}): '{inner[:24]}'")
    return errs


def page_texts(svg):
    """Visible strings of one page in drawing order (header page number excluded) — for fidelity checks."""
    out = []
    for m in TEXT_RE.finditer(svg):
        a, inner = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        if abs(float(_attr(a, "y", 0)) - HEADER_Y) < 0.6 and float(_attr(a, "font-size", 0)) <= 13:
            continue
        out.append(html.unescape(inner))
    return out


def build(spec, project=None, spec_dir=None, extra=None):
    """Build every page of `spec`. extra = {layout_name: (fn, needs_gm, role)} for deck-specific layouts.
    Returns (project_dir, errors, page_texts_by_stem)."""
    spec_dir = Path(spec_dir or ROOT)
    lock = bool(spec.get("lock_content"))
    prim.LOCK = lock
    project = project or spec.get("project") or "video_deck"
    theme = spec.get("theme")
    P = init_project(project, lock, theme)
    course = spec.get("course", "")
    brand = spec.get("brand", "" if lock else "INSIGHTLEARNING")
    registry = {**layouts.LAYOUTS, **(extra or {})}
    accessible = bool(spec.get("accessible"))           # low-vision mode (design-system §4-1)
    prim.MIN_FW = 500 if accessible else 0
    prim.CONTRAST = accessible
    errors, notes, dump = [], [], {}
    for i, p in enumerate(spec.get("pages") or [], 1):
        lay = p.get("layout")
        if lay not in registry:
            errors.append(f"page {i}: unknown layout '{lay}' — one of {', '.join(registry)}")
            continue
        fn, needs_gm, role = registry[lay]
        if p.get("src"):
            src = Path(p["src"]) if Path(p["src"]).is_absolute() else spec_dir / p["src"]
            if src.exists():
                dst = P / "images" / f"p{i:02d}_{slug(src.stem)}{src.suffix.lower()}"
                shutil.copy(src, dst)
                p["_image_href"] = f"../images/{dst.name}"
            else:
                errors.append(f"page {i}: image not found: {src}")
        if needs_gm and not p.get("gm") and not lock:
            errors.append(f"page {i} ({lay}): 'gm' (one-line governing message) is required on content pages")
        prim.WARNINGS.clear()
        prim.MIN_FS = (p.get("min_fs") or spec.get("min_fs") or 20) if accessible else 0
        has_gm = bool(needs_gm and p.get("gm"))
        layouts.BOT = BODY_BOTTOM if has_gm or role != "content" else 600   # no GM pill → content may use its space
        p["_page"] = i
        for im in p.get("images") or []:               # photos layout: copy each image into the project
            src = Path(im["src"]) if Path(im["src"]).is_absolute() else spec_dir / im["src"]
            if src.exists():
                dst = P / "images" / f"p{i:02d}_{slug(src.stem)}{src.suffix.lower()}"
                shutil.copy(src, dst)
                im["_href"] = f"../images/{dst.name}"
            else:
                errors.append(f"page {i}: image not found: {src}")
        body = fn(p)
        stem = p.get("stem") or {"cover": f"{i:02d}_cover", "ending": f"{i:02d}_ending"}.get(
            role, f"{i:02d}_chapter_{lay}" if role == "chapter" else f"{i:02d}_{lay}")
        show_title = p.get("title") if (lay in layouts.SHELL_TITLE or p.get("shell_title")
                                        or (lay in ("icon_list", "hub") and p.get("title"))) else None
        if lay == "agenda" and not show_title and not lock:
            show_title = "강의 | 순서"
        svg = frame.page(body, course=course if role != "cover" else spec.get("cover_label", course),
                         num=None if role in ("cover", "ending") else i, section=p.get("section"),
                         title_text=show_title, gm=p.get("gm") if needs_gm and p.get("gm") else None, brand=brand)
        svg = themed(svg, theme)
        (P / "svg_output" / f"{stem}.svg").write_text(svg, encoding="utf-8")
        for w in prim.WARNINGS:
            print(f"  [WARN] page {i} ({lay}): {w}")
        errors += zone_check(svg, stem)
        dump[stem] = page_texts(svg)
        notes.append((stem, p.get("notes") or prim.plain(p.get("title", "")) or lay))

    with open(P / "notes" / "total.md", "w", encoding="utf-8") as f:
        f.write("\n".join(f"# {k}\n\n{v.strip()}\n" for k, v in notes))
    (P / "page_texts.json").write_text(json.dumps(dump, ensure_ascii=False, indent=1), encoding="utf-8")
    for e in errors:
        print(f"  [ERROR] {e}")
    print(f"video-slide build: {len(spec.get('pages') or [])} pages → {P / 'svg_output'} · errors: {len(errors)}"
          + (" · content-lock" if lock else ""))
    print(f"project: {project}")
    return P, errors, dump


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--project")
    a = ap.parse_args()
    spec = load(a.spec)
    _, errors, _ = build(spec, a.project or spec.get("project") or slug(Path(a.spec).stem),
                         Path(a.spec).resolve().parent)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
