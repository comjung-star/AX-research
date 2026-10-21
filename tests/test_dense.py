"""Dense Retriever의 외부 다운로드 없는 입력검증 테스트."""

import unittest

from ax_research.retrieval.dense import DenseRetriever


class DenseRetrieverTest(unittest.TestCase):
    def test_empty_documents_are_rejected_before_model_loading(self) -> None:
        with self.assertRaises(ValueError):
            DenseRetriever({})


if __name__ == "__main__":
    unittest.main()
