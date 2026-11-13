#!/usr/bin/env python3
"""finish.py — verify, render and deliver one edu-video deck.

Usage (repo root, AFTER total_md_split → finalize_svg → svg_to_pptx -s final):
    .claude/skills/slide/scripts/_py.sh .claude/skills/edu-video/scripts/finish.py <project> "<name>.pptx" [--dst DIR] [--no-render]

verify_deck must PASS (it reads <project>/.gm_band for the key-strip band). Renders to
output/<project>/_pptx_render/sNN.png + gridN.png — look at every grid before delivering.
Delivery: --dst, else $EDU_VIDEO_DST, else output/_deliver/.
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / ".claude/skills/generic-redesign/scripts"))
import render  # noqa: E402

ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("deliver")
ap.add_argument("--dst")
ap.add_argument("--no-render", action="store_true")
a = ap.parse_args()
dst = a.dst or os.environ.get("EDU_VIDEO_DST") or str(ROOT / "output" / "_deliver")
P = ROOT / "output" / a.project
pptxs = sorted(p for p in glob.glob(str(P / "exports" / "*.pptx")) if not p.endswith("_svg.pptx"))
if not pptxs:
    sys.exit("no native PPTX in exports/ — run svg_to_pptx.py <project> -s final first")
pptx = max(pptxs, key=os.path.getmtime)
today = date.today().isoformat()
st = {"project": a.project, "mode": f"edu-video ({today})", "stages": [
    {"stage": s, "status": "done", "completed_at": today} for s in
    ["content yaml", "build_deck (svg + plan + notes, sequential)", "zone/a11y check",
     "total_md_split", "finalize_svg", "svg_to_pptx -s final"]]}
json.dump(st, open(P / "pipeline_status.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

res = subprocess.run([sys.executable, str(ROOT / ".claude/skills/slide/scripts/verify_deck.py"), str(P)],
                     capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
tail = [l for l in res.stdout.splitlines() if "verify_deck" in l or "✗" in l]
print("\n".join(tail) or res.stdout[-800:])
z = zipfile.ZipFile(pptx)
print("zip:", z.testzip() or "OK", len([n for n in z.namelist() if n.startswith("ppt/slides/slide")]), "slides")
if res.returncode != 0 or "PASS" not in "".join(tail):
    sys.exit("verify failed — not delivering")

how = "skipped"
if not a.no_render:
    out = str(P / "_pptx_render")
    how = render.render_pptx(pptx, out) or render.render_svgs(str(P / "svg_final"), out) or "none"
    print(f"render: {how} · grids: {render.grids(out)} → {out}")
    if how == "svg-approx":
        print("  [note] approximate render — check overflow/overlap only; final typography check in PowerPoint")
os.makedirs(dst, exist_ok=True)
target = os.path.join(dst, a.deliver)
shutil.copy(pptx, target)
st["stages"] += [{"stage": "verify_deck", "status": "done", "result": "PASS"},
                 {"stage": "render review", "status": "done", "renderer": how},
                 {"stage": "delivery", "status": "done", "artifacts": [target]}]
json.dump(st, open(P / "pipeline_status.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("delivered:", target)
