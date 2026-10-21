"""BM25 검색기의 최소 동작 테스트.

외부 dependency가 설치되지 않은 환경에서는 skip됩니다.
"""

import unittest


class BM25RetrieverTest(unittest.TestCase):
    def test_simple_korean_keyword_ranking(self) -> None:
        try:
            from ax_research.retrieval.bm25 import BM25Retriever
            retriever = BM25Retriever(
                {
                    "A": "[PROBLEM] 품질 불량 원인 분석이 오래 걸린다",
                    "B": "[PROBLEM] 고객 문의 답변이 반복된다",
                    "C": "[PROBLEM] 생산 설비의 품질 결함을 분석한다",
                }
            )
        except RuntimeError as exc:
            self.skipTest(str(exc))

        result = retriever.search("품질 불량 원인", top_k=2)
        self.assertEqual(result[0].case_id, "A")
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
