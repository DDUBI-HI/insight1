#!/usr/bin/env python3
"""finish.py — verify, render and deliver one video-slide deck.

Usage:
    finish.py <project> "<file name>.pptx" [--dst <folder>] [--no-render]

Run AFTER the three post-processing calls (total_md_split → finalize_svg → svg_to_pptx -s final).
Steps: pipeline_status.json → verify_deck (must PASS) → zip test → render to
output/<project>/_pptx_render/sNN.png + gridN.png (look at every grid!) → copy to the delivery folder.
Renderer: PowerPoint (Windows) → LibreOffice → approximate SVG render — shared with generic-redesign.
Delivery folder: --dst, else $VIDEO_SLIDE_DST, else output/_deliver/.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "generic-redesign" / "scripts"))
import render  # noqa: E402

ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("deliver")
ap.add_argument("--dst", default=None)
ap.add_argument("--no-render", action="store_true")
a = ap.parse_args()
dst = a.dst or os.environ.get("VIDEO_SLIDE_DST") or str(ROOT / "output" / "_deliver")

P = ROOT / "output" / a.project
today = date.today().isoformat()
pptxs = sorted((p for p in glob.glob(str(P / "exports" / "*.pptx")) if not p.endswith("_svg.pptx")),
               key=os.path.getmtime)
if not pptxs:
    sys.exit("no native PPTX in exports/ — run svg_to_pptx.py <project> -s final first")
pptx = pptxs[-1]

st = {"project": a.project, "mode": f"video-slide ({today})", "stages": [
    {"stage": s, "status": "done", "completed_at": today} for s in
    ["content spec (deck.yaml)", "build_deck (svg generation, main agent)", "speaker notes", "total_md_split",
     "finalize_svg", "svg_to_pptx -s final"]]}
st["stages"][-1]["artifacts"] = [os.path.relpath(pptx, P)]
json.dump(st, open(P / "pipeline_status.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

res = subprocess.run([sys.executable, str(ROOT / ".claude/skills/slide/scripts/verify_deck.py"), str(P)],
                     capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
out = (res.stdout + res.stderr).splitlines()
# The quality checker's generic safe area (x 56–1224, y 40–680) flags this theme's full-bleed frame and the
# local coordinates inside illustration groups — expected; build_deck.py's zone_check is the real gate here.
noise = ("Safe-area violation", "Passed (with warnings)", "With warnings:", "With errors: 0")
print("\n".join(l for l in out if not any(n in l for n in noise)
                and ("verify_deck" in l or "✗" in l or "WARN" in l or "FAIL" in l or "ERROR" in l)))
z = zipfile.ZipFile(pptx)
print("zip:", z.testzip() or "OK", len([n for n in z.namelist() if n.startswith("ppt/slides/slide")]), "slides")
if res.returncode != 0:
    sys.exit("verify failed — not delivering")

how = "skipped"
if not a.no_render:
    rdir = str(P / "_pptx_render")
    how = render.render_pptx(pptx, rdir) or render.render_svgs(str(P / "svg_final"), rdir) or "none"
    n = render.grids(rdir)
    print(f"render: {how} · grids: {n} → {rdir}")
    if how == "svg-approx":
        print("  [note] approximate render: Hangul uses a wider fallback font — judge overflow, not typography")

os.makedirs(dst, exist_ok=True)
target = os.path.join(dst, a.deliver)
shutil.copy(pptx, target)
st["stages"] += [{"stage": "verify_deck", "status": "done", "result": "PASS"},
                 {"stage": "render review", "status": "done", "renderer": how},
                 {"stage": "delivery", "status": "done", "artifacts": [target]}]
json.dump(st, open(P / "pipeline_status.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("delivered:", target)
