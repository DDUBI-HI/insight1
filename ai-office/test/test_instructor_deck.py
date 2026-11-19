"""tools/instructor_deck.py 시험 — 작은 가짜 강사풀 PPT 를 만들어 강사 장 추가를 확인한다.
    python -m unittest discover -s ai-office/test -p "test_*.py"   (python-pptx 필요)"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

TOOL = Path(__file__).resolve().parents[1] / "tools" / "instructor_deck.py"


def box(slide, text, x, y, w=3.0, h=0.4, size=10):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    lines = text if isinstance(text, list) else [text]
    tf = tb.text_frame
    tf.text = lines[0]
    tf.paragraphs[0].runs[0].font.size = Pt(size)
    for line in lines[1:]:
        p = tf.add_paragraph()
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
    return tb


def make_deck(path):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    s = prs.slides.add_slide(blank)
    box(s, "검증된 2명의 전문 강사", 1, 1, 6)
    s = prs.slides.add_slide(blank)
    box(s, "02", 10, 0.2, 1)
    box(s, "2인 전원 · 1/1", 1, 1, 4)
    t = s.shapes.add_table(3, 4, Inches(0.6), Inches(2), Inches(12), Inches(1.2)).table
    for c, h in enumerate(["강사", "소속 · 직함", "핵심 전문 영역", "대표 수행 실적"]):
        t.cell(0, c).text = h
    for r, n in enumerate(["가강사", "나강사"], 1):
        for c, v in enumerate([n, "소속 " + n, "분야 " + n, "실적 " + n]):
            t.cell(r, c).text = v
    for i, (n, lab) in enumerate([("가강사", "학력 · 자격"), ("나강사", "경력 · 활동")], 3):
        s = prs.slides.add_slide(blank)
        box(s, "INSIGHT LEARNING · 강사풀", 0.6, 0.2, 6)
        box(s, f"{i:02d}", 10, 0.2, 1)
        box(s, "INSIGHT LEARNING  ·  AI INSTRUCTOR", 1, 1)
        box(s, n, 1, 1.4, size=30)
        box(s, ["소속 첫 줄 " + n, "소속 둘째 줄"], 1, 2.0)
        box(s, "전문 분야", 1, 3.0)
        box(s, ["분야 하나", "분야 둘", "분야 셋"], 1, 3.3)
        box(s, lab, 1, 4.6)
        box(s, ["학력 하나", "자격 둘"], 1, 4.9)
        box(s, "STRENGTH  ·  핵심 강점", 5, 1)
        box(s, "강점 제목 " + n * 5, 5, 1.3, 7)
        box(s, "강점 설명 " + n * 20, 5, 1.6, 7)
        box(s, "REFERENCE  ·  대표 수행 실적", 5, 2.7)
        box(s, ["실적 하나 " + n, "실적 둘"], 5, 3.0)
        box(s, ["실적 셋", "실적 넷"], 9, 3.0)
        box(s, "PROGRAM  ·  보유 과정 · 콘텐츠", 5, 5.2)
        box(s, ["과정 하나 " + n * 3], 5, 5.5, 7)
    s = prs.slides.add_slide(blank)
    box(s, "05", 10, 0.2, 1)
    box(s, "2인 풀에서 복수 강사 투입", 1, 1, 6)
    prs.save(str(path))


def run(*args):
    r = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, json.loads(r.stdout)


class DeckTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.deck = self.d / "강사풀 원본.pptx"
        make_deck(self.deck)
        self.before = self.deck.read_bytes()

    def profile(self, name="다강사", **kw):
        p = {"name": name, "affiliation": ["새 소속"], "specialties": ["분야 A", "분야 B"], "education_label": "경력 · 자격",
             "education": ["학력 A"], "strength_title": "강점 제목", "strength_body": "강점 설명입니다.",
             "references": ["실적 A", "실적 B", "실적 C"], "programs": ["과정 A"]}
        p.update(kw)
        f = self.d / f"{name}.json"
        f.write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
        return f

    def test_analyze(self):
        code, info = run("analyze", self.deck)
        self.assertEqual(code, 0)
        self.assertEqual(info["count"], 2)
        self.assertEqual(info["profile_slides"], [3, 4])
        self.assertEqual(info["names"], ["가강사", "나강사"])
        self.assertEqual(info["fields"]["specialties"]["max_lines"], 3)

    def test_add(self):
        out = self.d / "결과.pptx"
        code, res = run("add", self.deck, self.profile(), out)
        self.assertEqual(code, 0, res)
        self.assertEqual(res["new_slide"], 5)
        self.assertEqual(res["count"], 3)
        self.assertEqual(self.deck.read_bytes(), self.before, "원본은 그대로")
        prs = Presentation(str(out))
        slides = list(prs.slides)
        self.assertEqual(len(slides), 6)
        texts = [sh.text_frame.text for sh in slides[4].shapes if sh.has_text_frame]
        self.assertIn("다강사", texts)
        self.assertIn("경력 · 자격", texts)
        self.assertIn("05", texts, "새 장의 쪽 번호")
        self.assertIn("06", [sh.text_frame.text for sh in slides[5].shapes if sh.has_text_frame], "뒤 장 쪽 번호가 밀린다")
        self.assertIn("검증된 3명의 전문 강사", [sh.text_frame.text for sh in slides[0].shapes if sh.has_text_frame])
        tbl = [sh for sh in slides[1].shapes if sh.has_table][0].table
        self.assertEqual(len(tbl.rows), 4)
        self.assertEqual(tbl.cell(3, 0).text, "다강사")
        refs_left = [sh for sh in slides[4].shapes if sh.has_text_frame and sh.text_frame.text.startswith("실적 A")]
        self.assertTrue(refs_left, "실적이 두 단으로 나뉜다")
        # 같은 이름은 다시 넣지 않는다
        code, res = run("add", out, self.profile("다강사"), self.d / "두번째.pptx")
        self.assertEqual(res["code"], "exists")
        # 결과 파일 덮어쓰기 거부
        code, res = run("add", self.deck, self.profile("라강사"), out)
        self.assertEqual(res["code"], "out_exists")

    def test_overflow(self):
        code, res = run("add", self.deck, self.profile(specialties=["a", "b", "c", "d", "e"]), self.d / "x.pptx")
        self.assertEqual(code, 2)
        self.assertEqual(res["code"], "overflow")
        self.assertFalse((self.d / "x.pptx").exists())


if __name__ == "__main__":
    unittest.main()


class InstagramImagesTest(unittest.TestCase):
    def test_convert_and_pick(self):
        from PIL import Image
        d = Path(tempfile.mkdtemp())
        src = d / "out"; src.mkdir()
        for i in range(1, 14):
            Image.new("RGB", (1080, 1440), (10, 20, 30)).save(src / f"{i:02d}-card.png")
        Image.new("RGB", (100, 100)).save(src / "overview.png")
        tool = Path(__file__).resolve().parents[1] / "tools" / "instagram_images.py"
        r = subprocess.run([sys.executable, str(tool), str(src), str(d / "ig")], capture_output=True, text=True, encoding="utf-8")
        res = json.loads(r.stdout)
        self.assertTrue(res["ok"])
        self.assertEqual((res["total"], res["used"]), (13, 10))
        self.assertTrue(res["files"][-1].endswith("13-card.jpg"), "마지막 장(마무리)은 남긴다")
        self.assertEqual(res["dropped"], ["10-card.png", "11-card.png", "12-card.png"])
        im = Image.open(res["files"][0])
        self.assertEqual((im.size, im.format), ((1080, 1350), "JPEG"))
