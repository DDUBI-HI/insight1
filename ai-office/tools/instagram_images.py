#!/usr/bin/env python3
"""카드뉴스 PNG → 인스타그램 게시용 JPEG.

    python instagram_images.py <out 폴더(01-cover.png …)> <저장 폴더> [--max 10] [--size 1080x1350]

- 인스타그램 게시 API 는 JPEG 만 받고, 세로는 4:5(1080×1350)까지다.
  카드(3:4, 1080×1440)를 줄여 4:5 판에 가운데 놓고 양옆을 카드 가장자리 색으로 채운다(글자를 자르지 않음).
- 한 게시물은 최대 10장 → 넘으면 앞 (max-1)장 + 마지막 장(마무리 CTA).
- overview.png 는 뺀다. 결과 JSON 을 출력한다. Pillow 필요(slide-svg 가상환경에 있음).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image


def edge_color(img):
    w, h = img.size
    px = [img.getpixel((x, y)) for x in (0, w - 1) for y in range(0, h, max(1, h // 40))]
    return tuple(sum(c[i] for c in px) // len(px) for i in range(3))


def convert(src: Path, dst: Path, size):
    W, H = size
    img = Image.open(src).convert("RGB")
    scale = min(W / img.width, H / img.height)
    nw, nh = round(img.width * scale), round(img.height * scale)
    canvas = Image.new("RGB", (W, H), edge_color(img))
    canvas.paste(img.resize((nw, nh), Image.LANCZOS), ((W - nw) // 2, (H - nh) // 2))
    canvas.save(dst, "JPEG", quality=92, optimize=True, progressive=False)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    src, dst = Path(argv[0]), Path(argv[1])
    mx = int(argv[argv.index("--max") + 1]) if "--max" in argv else 10
    size = tuple(int(x) for x in (argv[argv.index("--size") + 1] if "--size" in argv else "1080x1350").split("x"))
    pngs = sorted(p for p in src.glob("*.png") if p.name.lower() != "overview.png")
    if not pngs:
        print(json.dumps({"ok": False, "error": f"PNG 가 없습니다: {src}"}, ensure_ascii=False))
        return 2
    used = pngs if len(pngs) <= mx else pngs[: mx - 1] + [pngs[-1]]
    dropped = [p.name for p in pngs if p not in used]
    dst.mkdir(parents=True, exist_ok=True)
    files = []
    for i, p in enumerate(used, 1):
        out = dst / f"{i:02d}-{p.stem}.jpg"
        convert(p, out, size)
        files.append(str(out))
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"ok": True, "files": files, "total": len(pngs), "used": len(used), "dropped": dropped, "size": f"{size[0]}x{size[1]}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
