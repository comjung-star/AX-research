"""Kiwi + BM25 기반 Sparse Retrieval.

쉽게 말하면:
- Kiwi: 한국어 문장을 형태소 단위로 나눕니다.
- BM25: Query와 Case 문서에 같은 핵심 단어가 얼마나 잘 등장하는지 점수화합니다.

RQ1에서 Single-query BM25와 Multi-Perspective + BM25는
반드시 이 동일 구현을 공유합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RankedCase:
    """검색결과 한 건. score가 클수록 관련도가 높습니다."""

    case_id: str
    score: float


class KiwiTokenizer:
    """RQ1 v1에서 확정한 한국어 tokenizer.

    v1에서는 임의의 품사 가중치나 사용자 사전을 넣지 않습니다.
    그런 조정이 필요하면 Dev 실험 근거를 남기고 새 config 버전에서 검증합니다.
    """

    def __init__(self) -> None:
        try:
            from kiwipiepy import Kiwi
        except ImportError as exc:
            raise RuntimeError(
                "Kiwi를 사용하려면 'kiwipiepy' 패키지가 필요합니다. "
                "requirements-rq1.txt를 설치해 주세요."
            ) from exc
        self._kiwi = Kiwi()

    def tokenize(self, text: str) -> list[str]:
        """기호를 제외한 Kiwi 형태소를 소문자로 반환합니다.

        조사/어미를 임의로 제거하지 않는 이유:
        baseline에 숨은 튜닝을 추가하지 않기 위해서입니다.
        흔한 형태소는 BM25의 IDF에서 자연스럽게 영향력이 낮아집니다.
        """

        tokens: list[str] = []
        for token in self._kiwi.tokenize(text):
            form = token.form.strip().lower()
            if not form:
                continue
            if token.tag.startswith("S"):
                continue
            tokens.append(form)
        return tokens


class BM25Retriever:
    """case_id -> Problem View text를 검색하는 BM25 Retriever."""

    def __init__(self, documents: Mapping[str, str]) -> None:
        if not documents:
            raise ValueError("documents must not be empty")

        try:
            from rank_bm25 import BM25Okapi
        except ImportError as exc:
            raise RuntimeError(
                "BM25를 사용하려면 'rank-bm25' 패키지가 필요합니다."
            ) from exc

        self._tokenizer = KiwiTokenizer()
        self._case_ids = list(documents.keys())
        tokenized_documents = [
            self._tokenizer.tokenize(documents[case_id])
            for case_id in self._case_ids
        ]
        self._bm25 = BM25Okapi(tokenized_documents)

    def search(self, query: str, top_k: int) -> list[RankedCase]:
        """Query를 검색해 점수 높은 순으로 Top-K를 반환합니다."""

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        scores = self._bm25.get_scores(self._tokenizer.tokenize(query))
        ranked = sorted(
            (
                RankedCase(case_id=case_id, score=float(score))
                for case_id, score in zip(self._case_ids, scores, strict=True)
            ),
            key=lambda item: (-item.score, item.case_id),
        )
        return ranked[:top_k]
