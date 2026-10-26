import unittest
from collections import Counter
from html.parser import HTMLParser

from prototype.core import ROOT


class ResearchPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class ResearchPopupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "prototype/web/index.html").read_text(encoding="utf-8")
        cls.parser = ResearchPageParser()
        cls.parser.feed(cls.html)
        cls.by_id = {attrs["id"]: (tag, attrs) for tag, attrs in cls.parser.elements if "id" in attrs}

    def test_two_shortcuts_open_labeled_native_dialogs(self):
        for button_id, dialog_id in (("architecture-button", "architecture-dialog"), ("paper-status-button", "paper-status-dialog")):
            tag, attrs = self.by_id[button_id]
            self.assertEqual(tag, "button")
            self.assertEqual(attrs["type"], "button")
            self.assertEqual(attrs["aria-haspopup"], "dialog")
            self.assertEqual(attrs["aria-controls"], dialog_id)
            dialog_tag, dialog_attrs = self.by_id[dialog_id]
            self.assertEqual(dialog_tag, "dialog")
            self.assertIn(dialog_attrs["aria-labelledby"], self.by_id)
            self.assertIn(dialog_attrs["aria-describedby"], self.by_id)
        counts = Counter(attrs["id"] for tag, attrs in self.parser.elements if "id" in attrs)
        self.assertTrue(all(count == 1 for count in counts.values()))

    def test_explanatory_diagram_preserves_three_example_branches(self):
        branches = [attrs for tag, attrs in self.parser.elements if "architecture-branch" in attrs.get("class", "").split()]
        self.assertEqual(len(branches), 3)
        self.assertEqual(len({branch["aria-labelledby"] for branch in branches}), 3)
        self.assertIn("실제 개수와 내용은 입력에 따라 달라집니다", self.html)
        self.assertIn("한 줄의 통합 순위로 합치지 않습니다", self.html)
        self.assertIn("3가지 유사도 점수의 평균", self.html)

    def test_summary_distinguishes_dev_performance_history_and_unverified_manuscript(self):
        for required in ("47.64%", "27.73%", "45.33%", "AI-Silver", "v1 코퍼스 100개", "v2.3 84개", "완성 원고", "인과관계"):
            self.assertIn(required, self.html)
        self.assertIn("완료율을 표시하지 않습니다", self.html)
        self.assertIn("관련 사례가 없는 관점 18개", self.html)

    def test_popup_assets_are_local_and_do_not_inject_inline_scripts(self):
        scripts = [attrs for tag, attrs in self.parser.elements if tag == "script"]
        self.assertTrue(any(attrs.get("src") == "/research.js" for attrs in scripts))
        self.assertTrue(all(attrs.get("src", "").startswith("/") and "defer" in attrs for attrs in scripts))
        self.assertFalse(any(name.startswith("on") for tag, attrs in self.parser.elements for name in attrs))
        source = (ROOT / "prototype/web/research.js").read_text(encoding="utf-8")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("innerHTML", source)


if __name__ == "__main__":
    unittest.main()
