#!/usr/bin/env python3
"""extract_source.py — turn client source decks into reviewable text + page renders.

Usage:
    extract_source.py <workdir> [stem=]<file> [[stem=]<file> ...]

For each input it writes, under <workdir>:
    <stem>.md            text extraction (ppt_to_md / pdf_to_md / doc_to_md)
    <stem>_files/        embedded pictures — instructor photos etc.
    r_<stem>/sNN.png     one PNG per slide/page
    r_<stem>/gridN.png   2×2 contact sheets for quick visual review

Rendering: PDF → PyMuPDF (any host). PPTX → PowerPoint (Windows) or LibreOffice (cloud/Linux/mac).
With neither, PPTX slide images are skipped (text + pictures still extracted) — say so to the user.
Legacy .ppt needs PowerPoint or LibreOffice to convert to .pptx first.

Sources are only read — never moved or modified. Short ASCII stems are recommended
(e.g. `komico=/path/코미코 제안서.pptx`).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
SK = ROOT / ".claude" / "skills" / "slide" / "scripts" / "source_to_md"
_venv = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python3")
PY = str(_venv) if _venv.exists() else sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def ppt_to_pptx(local, work):
    pptx = work / f"{local.stem}.pptx"
    if render.has_powerpoint():
        ps = (f"$pp = New-Object -ComObject PowerPoint.Application; $p = $pp.Presentations.Open('{local}', $true, $false, $false); "
              f"$p.SaveAs('{pptx}', 24); $p.Close(); $pp.Quit()")
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
        return pptx
    out = render.soffice_convert(str(local), "pptx", str(work))
    return Path(out) if out else None


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    work = Path(sys.argv[1]).resolve()
    work.mkdir(parents=True, exist_ok=True)
    for arg in sys.argv[2:]:
        if "=" in arg and not os.path.exists(arg):
            stem, path = arg.split("=", 1)
        else:
            stem, path = "", arg
        src = Path(path).resolve()
        stem = stem or src.stem
        ext = src.suffix.lower()
        local = work / f"{stem}{ext}"
        if src != local:
            shutil.copy(src, local)          # work on a copy; the original stays untouched
        out = work / f"r_{stem}"
        how = None
        if ext in (".pptx", ".pptm", ".ppsx"):
            subprocess.run([PY, str(SK / "ppt_to_md.py"), str(local), "-o", str(work / f"{stem}.md")], env=ENV)
            how = render.render_pptx(str(local), str(out))
        elif ext == ".ppt":
            pptx = ppt_to_pptx(local, work)
            if not pptx:
                print(f"[skip] {src.name}: .ppt needs PowerPoint or LibreOffice to convert — ask the user for a .pptx/.pdf")
                continue
            subprocess.run([PY, str(SK / "ppt_to_md.py"), str(pptx), "-o", str(work / f"{stem}.md")], env=ENV)
            how = render.render_pptx(str(pptx), str(out))
        elif ext == ".pdf":
            subprocess.run([PY, str(SK / "pdf_to_md.py"), str(local), "-o", str(work / f"{stem}.md")], env=ENV)
            out.mkdir(exist_ok=True)
            render.render_pdf(str(local), str(out))
            how = "pymupdf"
        elif ext in (".docx", ".doc"):
            subprocess.run([PY, str(SK / "doc_to_md.py"), str(local), "-o", str(work / f"{stem}.md")], env=ENV)
        else:
            print(f"[skip] unsupported: {src}")
            continue
        n = render.grids(str(out)) if out.exists() and any(out.glob("s*.png")) else 0
        note = "" if how or ext in (".docx", ".doc") else " · [WARN] no slide renderer (PowerPoint/LibreOffice) — text + pictures only"
        print(f"[ok] {stem}: {work / (stem + '.md')} · renders {n and len(list(out.glob('s*.png')))} via {how} · grids {n}{note}")


if __name__ == "__main__":
    main()
