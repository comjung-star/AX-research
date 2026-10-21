"""Kiwi + BM25 Sparse Retrieval baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..data import AXCase


@dataclass(frozen=True)
class RankedCase:
    case_id: str
    score: float


class KiwiBM25Retriever:
    """한국어 형태소 분석(Kiwi) 후 BM25로 검색하는 baseline.

    Kiwi는 한국어 조사/어미를 분리해 lexical matching을 안정화합니다.
    BM25 자체는 의미검색이 아니라 키워드 기반 검색입니다.
    """

    def __init__(self, cases: Sequence[AXCase]):
        try:
            from kiwipiepy import Kiwi
            from rank_bm25 import BM25Okapi
        except ImportError as exc:
            raise RuntimeError(
                "BM25 실행에는 kiwipiepy와 rank-bm25가 필요합니다. "
                "pip install -r requirements-rq1.txt 로 설치하세요."
            ) from exc

        self._cases = list(cases)
        self._kiwi = Kiwi()
        tokenized_documents = [self._tokenize(case.problem_view_text()) for case in self._cases]
        self._bm25 = BM25Okapi(tokenized_documents)

    def _tokenize(self, text: str) -> list[str]:
        """검색에 도움이 되는 형태소만 남긴다."""
        useful_prefixes = ("N", "V", "M", "SL", "SN")
        tokens: list[str] = []
        for token in self._kiwi.tokenize(text):
            if token.tag.startswith(useful_prefixes) and len(token.form.strip()) >= 1:
                tokens.append(token.form.lower())
        return tokens

    def search(self, query: str, top_k: int | None = None) -> list[RankedCase]:
        """Query를 검색하고 점수 내림차순으로 사례를 반환한다."""
        query_tokens = self._tokenize(query)
        scores = self._bm25.get_scores(query_tokens)
        ranked = sorted(
            (RankedCase(case.case_id, float(score)) for case, score in zip(self._cases, scores)),
            key=lambda x: x.score,
            reverse=True,
        )
        return ranked if top_k is None else ranked[:top_k]
