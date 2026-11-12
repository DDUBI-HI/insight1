#!/usr/bin/env python3
"""gallery.py — draw every library illustration on one sheet: output/_vs_gallery/illustrations.svg (+ .png
when Playwright/Chromium is available). Use it to choose an `illust:` key or to review a new drawing."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "vkit"))
import illust  # noqa: E402
import prim    # noqa: E402
from tokens import BODY, NAVY  # noqa: E402

ROOT = HERE.parents[3]
out = ROOT / "output" / "_vs_gallery"
out.mkdir(parents=True, exist_ok=True)
cols, cw, ch = 5, 256, 236
names = illust.names()
rows = (len(names) + cols - 1) // cols
W, H = cols * cw, rows * ch
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
     f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
for i, n in enumerate(names):
    x, y = (i % cols) * cw + 8, (i // cols) * ch + 6
    o.append(illust.place(n, x, y, 240, 180))
    o.append(prim.text(x + 120, y + 202, n, 15, 700, NAVY, "middle"))
    o.append(prim.text(x + 120, y + 222, illust.LIB[n][1], 13, 400, BODY, "middle"))
o.append("</svg>")
svg = out / "illustrations.svg"
svg.write_text("\n".join(o), encoding="utf-8")
print("gallery:", svg)

js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
      f"const p=await b.newPage({{viewport:{{width:{W},height:{H}}}}});await p.goto('file://{svg.as_posix()}');"
      f"await p.screenshot({{path:'{(out / 'illustrations.png').as_posix()}'}});await b.close();}})();")
try:
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=120)
    if r.returncode == 0:
        print("png:", out / "illustrations.png")
except (OSError, subprocess.TimeoutExpired):
    pass
