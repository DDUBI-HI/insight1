"""render.py — host-independent page rendering for generic-redesign.

Renderers, tried in order:
  1. PowerPoint COM   (Windows with Office)             — exact PPTX rendering
  2. LibreOffice      (soffice/libreoffice on PATH)      — PPTX → PDF → PNG, close to exact
  3. PyMuPDF on SVG   (always available via requirements) — renders svg_final/*.svg; approximate:
     Hangul falls back to a wider built-in CJK font, so text looks lighter/wider than Pretendard
     (useful for spotting overflow and overlap, not for judging typography)

All functions write sNN.png (1280 px wide) into `out` and return the renderer name or None.
"""
import glob
import os
import shutil
import subprocess
import tempfile


def _clear(out):
    os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(out, "s*.png")) + glob.glob(os.path.join(out, "grid*.png")):
        os.remove(f)


def find_soffice():
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    for p in (r"C:\Program Files\LibreOffice\program\soffice.exe", r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
              "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if os.path.exists(p):
            return p
    return None


def has_powerpoint():
    if os.name != "nt" or os.environ.get("GR_NO_POWERPOINT"):
        return False
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "try { $p = New-Object -ComObject PowerPoint.Application; $p.Quit(); 'ok' } catch { 'no' }"],
                           capture_output=True, text=True, timeout=60)
        return "ok" in r.stdout
    except Exception:
        return False


def render_pdf(pdf, out, start=1):
    import pymupdf
    doc = pymupdf.open(pdf)
    for i, pg in enumerate(doc, start):
        z = 1280 / max(pg.rect.width, 1)
        pg.get_pixmap(matrix=pymupdf.Matrix(z, z)).save(os.path.join(out, f"s{i:02d}.png"))
    return len(doc)


def _powerpoint(pptx, out):
    ps = (f"$pp = New-Object -ComObject PowerPoint.Application; $p = $pp.Presentations.Open('{os.path.abspath(pptx)}', $true, $false, $false); "
          f"$n=1; foreach ($sl in $p.Slides) {{ $sl.Export((Join-Path '{os.path.abspath(out)}' ('s{{0:D2}}.png' -f $n)), 'PNG', 1280, 720); $n++ }}; "
          f"$p.Close(); $pp.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, timeout=900)


def soffice_convert(src, fmt, outdir):
    """LibreOffice headless conversion (fmt: 'pdf' | 'pptx'). Returns the output path or None."""
    so = find_soffice()
    if not so:
        return None
    subprocess.run([so, "--headless", "--convert-to", fmt, "--outdir", outdir, src],
                   capture_output=True, timeout=900)
    p = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + "." + fmt)
    return p if os.path.exists(p) else None


def render_pptx(pptx, out):
    """Render a .pptx with PowerPoint, else LibreOffice. Returns 'powerpoint' | 'libreoffice' | None."""
    _clear(out)
    if has_powerpoint():
        try:
            _powerpoint(pptx, out)
            if glob.glob(os.path.join(out, "s*.png")):
                return "powerpoint"
        except Exception as e:
            print(f"[render] PowerPoint failed: {e}")
    with tempfile.TemporaryDirectory() as tmp:
        pdf = soffice_convert(os.path.abspath(pptx), "pdf", tmp)
        if pdf:
            render_pdf(pdf, out)
            return "libreoffice"
    return None


def render_svgs(svg_dir, out):
    """Approximate render of svg_final/*.svg with PyMuPDF. Returns 'svg-approx' | None."""
    import pymupdf
    _clear(out)
    svgs = sorted(glob.glob(os.path.join(svg_dir, "*.svg")))
    for i, f in enumerate(svgs, 1):
        doc = pymupdf.open(f)
        pg = doc[0]
        z = 1280 / max(pg.rect.width, 1)
        pg.get_pixmap(matrix=pymupdf.Matrix(z, z)).save(os.path.join(out, f"s{i:02d}.png"))
    return "svg-approx" if svgs else None


def grids(out):
    """2×2 contact sheets gridN.png from sNN.png. Returns the number of grids."""
    from PIL import Image
    ims = sorted(glob.glob(os.path.join(out, "s*.png")))
    for k in range(0, len(ims), 4):
        g = Image.new("RGB", (2560, 1440), "white")
        for j, f in enumerate(ims[k:k + 4]):
            im = Image.open(f).convert("RGB")
            im.thumbnail((1280, 720))
            g.paste(im, ((j % 2) * 1280, (j // 2) * 720))
        g.resize((1920, 1080)).save(os.path.join(out, f"grid{k // 4 + 1}.png"))
    return (len(ims) + 3) // 4
