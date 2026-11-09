#!/usr/bin/env python3
"""finish.py — verify, render, and deliver one generic-redesign deck.

Usage:
    finish.py <project> "<deliver file name>.pptx" [--dst <folder>] [--no-render]

Run AFTER the three post-processing calls (total_md_split → finalize_svg → svg_to_pptx -s final).
Steps: pipeline_status.json → verify_deck (must PASS) → zip test → render to
output/<project>/_pptx_render/sNN.png + gridN.png (review these images!) → copy to the delivery folder.

Render: PowerPoint (Windows) → LibreOffice → approximate SVG render (PyMuPDF). The renderer used is printed;
'svg-approx' means wider fallback Hangul font — check for overflow, not typography.

Delivery folder: --dst, else $GENERIC_REDESIGN_DST, else ~/OneDrive/바탕 화면/김주영 업무폴더/범용과정_리디자인
when that folder's parent exists (the user's Windows PC), else output/_deliver/ (cloud sessions — hand the
file to the user from there).
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
_venv = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python3")
PY = str(_venv) if _venv.exists() else sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
_ONEDRIVE = os.path.join(os.path.expanduser("~"), "OneDrive", "바탕 화면", "김주영 업무폴더", "범용과정_리디자인")


def default_dst():
    if os.environ.get("GENERIC_REDESIGN_DST"):
        return os.environ["GENERIC_REDESIGN_DST"]
    if os.path.isdir(os.path.dirname(_ONEDRIVE)):
        return _ONEDRIVE
    return str(ROOT / "output" / "_deliver")


ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("deliver")
ap.add_argument("--dst", default=None)
ap.add_argument("--no-render", action="store_true", help="skip rendering entirely")
a = ap.parse_args()
dst = a.dst or default_dst()

P = ROOT / "output" / a.project
today = date.today().isoformat()
pptxs = sorted(p for p in glob.glob(str(P / "exports" / "*.pptx")) if not p.endswith("_svg.pptx"))
if not pptxs:
    sys.exit("no native PPTX in exports/ — run svg_to_pptx.py <project> -s final first")
pptx = pptxs[-1]

st = {"project": a.project, "mode": f"generic-redesign ({today})", "stages": [
    {"stage": s, "status": "done", "completed_at": today} for s in
    ["source extraction", "generalization pass", "slide-plan + validate", "design_spec",
     "svg generation (sequential, main agent)", "speaker notes", "total_md_split", "finalize_svg", "svg_to_pptx -s final"]]}
st["stages"][-1]["artifacts"] = [os.path.relpath(pptx, P)]
json.dump(st, open(P / "pipeline_status.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

res = subprocess.run([PY, str(ROOT / ".claude/skills/slide/scripts/verify_deck.py"), str(P)],
                     capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
tail = [l for l in res.stdout.splitlines() if "verify_deck" in l or "✗" in l]
print("\n".join(tail))
z = zipfile.ZipFile(pptx)
print("zip:", z.testzip() or "OK", len([n for n in z.namelist() if n.startswith("ppt/slides/slide")]), "slides")
if "PASS" not in "".join(tail):
    sys.exit("verify failed — not delivering")

how = "skipped"
if not a.no_render:
    out = str(P / "_pptx_render")
    how = render.render_pptx(pptx, out) or render.render_svgs(str(P / "svg_final"), out) or "none"
    n = render.grids(out)
    print(f"render: {how} · grids: {n} → {out}")
    if how == "svg-approx":
        print("  [note] approximate render (no PowerPoint/LibreOffice): Hangul uses a wider fallback font — "
              "judge overflow/overlap, not typography; tell the user the final check should be done in PowerPoint")

os.makedirs(dst, exist_ok=True)
target = os.path.join(dst, a.deliver)
shutil.copy(pptx, target)
st["stages"] += [{"stage": "verify_deck", "status": "done", "result": "PASS"},
                 {"stage": "render review", "status": "done", "renderer": how},
                 {"stage": "delivery", "status": "done", "artifacts": [target]}]
json.dump(st, open(P / "pipeline_status.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("delivered:", target)
