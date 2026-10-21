"""BGE-M3 기반 Dense Retrieval.

Dense Retrieval은 Query와 Case 문장을 embedding(숫자 벡터)으로 바꾼 뒤
벡터 방향이 얼마나 비슷한지(cosine similarity)로 검색합니다.

RQ1 v1에서는 Single Dense와 Multi-Perspective Dense가
동일한 BAAI/bge-m3 인코더를 공유합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class RankedCase:
    case_id: str
    score: float


class DenseRetriever:
    """SentenceTransformers를 이용한 BGE-M3 Dense Retriever."""

    def __init__(
        self,
        documents: Mapping[str, str],
        model_name: str = "BAAI/bge-m3",
        normalize_embeddings: bool = True,
        device: str | None = None,
    ) -> None:
        if not documents:
            raise ValueError("documents must not be empty")

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Dense Retrieval을 사용하려면 'sentence-transformers'가 필요합니다."
            ) from exc

        self.model_name = model_name
        self.normalize_embeddings = normalize_embeddings
        self._case_ids = list(documents.keys())
        self._model = SentenceTransformer(model_name, device=device)

        texts = [documents[case_id] for case_id in self._case_ids]

        # Case가 100건이므로 v1에서는 ANN/Vector DB를 쓰지 않고
        # 100개 전체를 직접 비교합니다. 근사검색 오차를 실험에서 제거하기 위함입니다.
        self._document_embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=normalize_embeddings,
            show_progress_bar=False,
        ).astype(np.float32)

    def search(self, query: str, top_k: int) -> list[RankedCase]:
        """Query와 모든 Case의 cosine similarity를 계산해 Top-K를 반환합니다."""

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        query_embedding = self._model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
        )[0].astype(np.float32)

        if self.normalize_embeddings:
            # normalize된 벡터끼리는 dot product가 cosine similarity입니다.
            scores = self._document_embeddings @ query_embedding
        else:
            doc_norm = np.linalg.norm(self._document_embeddings, axis=1)
            query_norm = np.linalg.norm(query_embedding)
            denominator = np.maximum(doc_norm * query_norm, 1e-12)
            scores = (self._document_embeddings @ query_embedding) / denominator

        ranked = sorted(
            (
                RankedCase(case_id=case_id, score=float(score))
                for case_id, score in zip(self._case_ids, scores, strict=True)
            ),
            key=lambda item: (-item.score, item.case_id),
        )
        return ranked[:top_k]
