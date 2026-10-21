"""BGE-M3 Dense Retrieval baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from ..data import AXCase


@dataclass(frozen=True)
class DenseRankedCase:
    case_id: str
    score: float


class BGEM3DenseRetriever:
    """BAAI/bge-m3 임베딩 + cosine similarity 검색기.

    Single Dense와 Multi-Perspective Dense가 같은 클래스/모델을 사용해야
    Perspective 분해 외의 모델 차이를 통제할 수 있습니다.
    """

    def __init__(self, cases: Sequence[AXCase], model_name: str = "BAAI/bge-m3"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Dense 실행에는 sentence-transformers가 필요합니다. "
                "pip install -r requirements-rq1.txt 로 설치하세요."
            ) from exc

        self._cases = list(cases)
        self._model_name = model_name
        self._model = SentenceTransformer(model_name)
        documents = [case.problem_view_text() for case in self._cases]
        self._case_embeddings = self._model.encode(
            documents,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    def search(self, query: str, top_k: int | None = None) -> list[DenseRankedCase]:
        """Query embedding과 Case embedding의 cosine similarity로 순위를 만든다."""
        query_embedding = self._model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0]

        # normalize_embeddings=True이므로 dot product가 cosine similarity와 같습니다.
        scores = np.dot(self._case_embeddings, query_embedding)
        order = np.argsort(-scores)
        ranked = [
            DenseRankedCase(self._cases[i].case_id, float(scores[i]))
            for i in order
        ]
        return ranked if top_k is None else ranked[:top_k]
