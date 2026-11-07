"""Regression gates for repaired multilingual BM25 and retrieval scope."""
import unittest
from ax_research.retrieval.bm25_repaired import RepairedKiwiTokenizer,RepairedBM25Retriever
from ax_research.retrieval.bm25 import KiwiTokenizer

class TestBM25Repair(unittest.TestCase):
    def setUp(self):
        self.old=KiwiTokenizer()
        self.new=RepairedKiwiTokenizer()
    def test_latin_and_digits_never_discarded(self):
        text="Equipment failure 2026."
        tokens=self.new.tokenize(text)
        self.assertTrue(any(any(c.isascii() and c.isalpha() for c in t) for t in tokens))
        self.assertTrue(any(any(c.isdigit() for c in t) for t in tokens))
        self.assertNotIn(".",tokens)
    def test_korean_content_preserved(self):
        words=self.new.tokenize("설비 고장 위험을 예측한다.")
        self.assertIn("설비",words)
        self.assertIn("고장",words)
    def test_english_only_document_searchable(self):
        docs={"a":"foobar alpha unique manufacturing equipment",
             "b":"korean line 품질 검사",
             "c":"sample staff recreation benefits"}
        r=RepairedBM25Retriever(docs)
        self.assertTrue(all(x>0 for x in r._bm25.doc_len))
        self.assertEqual(r.search(docs["a"],top_k=1)[0].case_id,"a")
        self.assertEqual({x.case_id for x in r.search(docs["a"])},set(docs))
    def test_empty_doc_never_accepted(self):
        with self.assertRaises(ValueError):
            RepairedBM25Retriever({"a":"", "b":"문서 있음"})
if __name__=="__main__":unittest.main()
