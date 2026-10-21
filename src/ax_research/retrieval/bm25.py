"""Kiwi + BM25 Sparse Retrieval.

BM25는 의미 벡터가 아니라 단어/형태소의 등장 패턴을 이용하는 비교 기준입니다.
Single BM25와 Multi-Perspective BM25가 이 동일 클래스를 공유합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from ..data import AXCase


@dataclass(frozen=True)
class RankedCase:
    case_id: str
    score: float


class KiwiTokenizer:
    """RQ1 v1.1의 한국어 형태소 tokenizer."""

    def __init__(self) -> None:
        try:
            from kiwipiepy import Kiwi
        except ImportError as exc:
            raise RuntimeError(
                "Kiwi 실행에는 kiwipiepy가 필요합니다. "
                "pip install -r requirements-rq1.txt 를 실행하세요."
            ) from exc
        self._kiwi = Kiwi()

    def tokenize(self, text: str) -> list[str]:
        tokens: list[str] = []
        for token in self._kiwi.tokenize(text):
            form = token.form.strip().lower()
            if not form or token.tag.startswith("S"):
                continue
            tokens.append(form)
        return tokens


class BM25Retriever:
    """case_id -> text 문서를 BM25로 검색합니다."""

    def __init__(self, documents: Mapping[str, str]) -> None:
        if not documents:
            raise ValueError("documents must not be empty")

        try:
            from rank_bm25 import BM25Okapi
        except ImportError as exc:
            raise RuntimeError(
                "BM25 실행에는 rank-bm25가 필요합니다."
            ) from exc

        self._case_ids = list(documents)
        self._tokenizer = KiwiTokenizer()
        corpus = [
            self._tokenizer.tokenize(documents[case_id])
            for case_id in self._case_ids
        ]
        self._bm25 = BM25Okapi(corpus)

    def search(
        self, query: str, top_k: int | None = None
    ) -> list[RankedCase]:
        scores = self._bm25.get_scores(self._tokenizer.tokenize(query))
        ranked = sorted(
            (
                RankedCase(case_id, float(score))
                for case_id, score in zip(self._case_ids, scores, strict=True)
            ),
            key=lambda x: (-x.score, x.case_id),
        )
        return ranked if top_k is None else ranked[:top_k]


class KiwiBM25Retriever(BM25Retriever):
    """기존 Runner와의 호환성을 위한 AXCase 입력 wrapper."""

    def __init__(self, cases: Sequence[AXCase]) -> None:
        documents = {case.case_id: case.problem_view_text() for case in cases}
        super().__init__(documents)
