#!/usr/bin/env python3
"""finish.py — verify → render → 강사 영역 미리보기 → 납품 (lecture-slide).

Usage:
    _py.sh .claude/skills/lecture-slide/scripts/finish.py <project> "<파일명>.pptx" [--dst DIR] [--no-render]

후처리 3단계(total_md_split → finalize_svg → svg_to_pptx -s final) 다음에 실행한다.
산출:
  output/<project>/_pptx_render/sNN.png · gridN.png    — 실제 렌더 (넘침·겹침 검수)
  output/<project>/_pptx_render/zoneN.png              — 오른쪽 30 % 강사 영역을 반투명으로 덮은 미리보기
  <dst>/<파일명>.pptx                                    — 기본 dst = $LECTURE_SLIDE_DST 또는 output/_deliver/
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
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "generic-redesign" / "scripts"))
import render  # noqa: E402  (shared renderer: PowerPoint → LibreOffice → SVG approx)

ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
SAFE_FRAC = 896 / 1280


def ensure_pretendard():
    """Linux 클라우드 세션: LibreOffice 렌더가 Pretendard를 쓰도록 fonts/PretendardVariable.woff2 → ~/.fonts TTF
    + fontconfig 별칭(Pretendard → Pretendard Variable). 실패해도 렌더는 대체 폰트로 계속한다."""
    if os.name == "nt" or sys.platform == "darwin" or not shutil.which("fc-list"):
        return
    if "Pretendard" in subprocess.run(["fc-list"], capture_output=True, text=True).stdout:
        return
    try:
        from fontTools.ttLib import TTFont
        fd = Path.home() / ".fonts"
        fd.mkdir(exist_ok=True)
        f = TTFont(str(ROOT / "fonts" / "PretendardVariable.woff2"))
        f.flavor = None
        f.save(str(fd / "PretendardVariable.ttf"))
        cf = Path.home() / ".config" / "fontconfig" / "fonts.conf"
        if not cf.exists():
            cf.parent.mkdir(parents=True, exist_ok=True)
            cf.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'
                          '<alias binding="same"><family>Pretendard</family><prefer><family>Pretendard Variable</family>'
                          '</prefer></alias></fontconfig>\n', encoding="utf-8")
        subprocess.run(["fc-cache", "-f"], capture_output=True)
        print("font: installed Pretendard for rendering")
    except Exception as e:  # fonttools/brotli missing etc.
        print(f"font: Pretendard not installed for rendering ({e}) — `pip install fonttools brotli` and rerun")


def zone_previews(out: str) -> int:
    """sNN.png 위에 강사 영역(오른쪽 30 %)을 반투명 회색 + 실루엣으로 덮어 2×2 zoneN.png를 만든다."""
    from PIL import Image, ImageDraw
    ims = sorted(glob.glob(os.path.join(out, "s[0-9]*.png")))
    for f in glob.glob(os.path.join(out, "zone*.png")):
        os.remove(f)
    tiles = []
    for p in ims:
        im = Image.open(p).convert("RGBA")
        w, h = im.size
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        x0 = int(w * SAFE_FRAC)
        d.rectangle([x0, 0, w, h], fill=(34, 41, 74, 70))
        cx, s = (x0 + w) // 2, h / 720
        d.ellipse([cx - 52 * s, 230 * s, cx + 52 * s, 340 * s], fill=(34, 41, 74, 120))        # head
        d.rounded_rectangle([cx - 120 * s, 350 * s, cx + 120 * s, h + 40 * s], radius=int(90 * s),
                            fill=(34, 41, 74, 120))                                             # body
        d.line([x0, 0, x0, h], fill=(225, 29, 72, 255), width=max(2, int(2 * s)))
        tiles.append(Image.alpha_composite(im, ov).convert("RGB"))
    for k in range(0, len(tiles), 4):
        g = Image.new("RGB", (2 * 1280, 2 * 720), "white")
        for j, im in enumerate(tiles[k:k + 4]):
            g.paste(im.resize((1280, 720)), ((j % 2) * 1280, (j // 2) * 720))
        g.resize((1920, 1080)).save(os.path.join(out, f"zone{k // 4 + 1}.png"))
    return (len(tiles) + 3) // 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("deliver")
    ap.add_argument("--dst")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--preserve-content", action="store_true",
                    help="원본 내용 보존 리디자인: GM 줄을 일부러 넣지 않았으므로 verify의 GM 실패만은 허용")
    a = ap.parse_args()
    P = ROOT / "output" / a.project
    dst = a.dst or os.environ.get("LECTURE_SLIDE_DST") or str(ROOT / "output" / "_deliver")
    pptxs = sorted(p for p in glob.glob(str(P / "exports" / "*.pptx")) if not p.endswith("_svg.pptx"))
    if not pptxs:
        sys.exit("no native PPTX in exports/ — run svg_to_pptx.py <project> -s final first")
    pptx = pptxs[-1]
    today = date.today().isoformat()
    st = {"project": a.project, "mode": f"lecture-slide ({today})", "stages": [
        {"stage": s, "status": "done", "completed_at": today} for s in
        ["deck.yaml → build.py (svg, notes, plan)", "total_md_split", "finalize_svg", "svg_to_pptx -s final"]]}
    st["stages"][-1]["artifacts"] = [os.path.relpath(pptx, P)]
    (P / "pipeline_status.json").write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")

    res = subprocess.run([sys.executable, str(ROOT / ".claude/skills/slide/scripts/verify_deck.py"), str(P)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    tail = [l for l in (res.stdout + res.stderr).splitlines() if "verify_deck" in l or "✗" in l]
    print("\n".join(tail))
    z = zipfile.ZipFile(pptx)
    print("zip:", z.testzip() or "OK", len([n for n in z.namelist() if n.startswith("ppt/slides/slide")]), "slides")
    fails = [l for l in tail if "✗" in l]
    if res.returncode != 0:
        if a.preserve_content and fails and all("governing-message" in l for l in fails):
            print("  [note] --preserve-content: GM lines intentionally omitted (no text may be added); all other checks passed")
        else:
            sys.exit("verify failed — not delivering")

    how = "skipped"
    if not a.no_render:
        out = str(P / "_pptx_render")
        ensure_pretendard()
        how = render.render_pptx(pptx, out) or render.render_svgs(str(P / "svg_final"), out) or "none"
        n = render.grids(out)
        zn = zone_previews(out)
        print(f"render: {how} · grids: {n} · zone previews: {zn} → {out}")
        if how == "svg-approx":
            print("  [note] approximate render — judge overflow/overlap only; final font check in PowerPoint")

    os.makedirs(dst, exist_ok=True)
    target = os.path.join(dst, a.deliver)
    shutil.copy(pptx, target)
    st["stages"] += [{"stage": "verify_deck", "status": "done", "result": "PASS"},
                     {"stage": "render review", "status": "done", "renderer": how},
                     {"stage": "delivery", "status": "done", "artifacts": [target]}]
    (P / "pipeline_status.json").write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    print("delivered:", target)


if __name__ == "__main__":
    main()
