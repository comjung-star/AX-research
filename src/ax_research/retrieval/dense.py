"""BAAI/bge-m3 Dense Retrieval.

문장을 embedding 벡터로 바꾸고 cosine similarity로 검색합니다.
Single Dense와 Multi-Perspective Dense가 반드시 이 동일 backbone을 사용합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from ..data import AXCase


@dataclass(frozen=True)
class RankedCase:
    case_id: str
    score: float


class DenseRetriever:
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
                "Dense Retrieval에는 sentence-transformers가 필요합니다."
            ) from exc

        self._case_ids = list(documents)
        self._normalize = normalize_embeddings
        self._model = SentenceTransformer(model_name, device=device)

        self._case_embeddings = self._model.encode(
            [documents[cid] for cid in self._case_ids],
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).astype(np.float32)

    def search(
        self, query: str, top_k: int | None = None
    ) -> list[RankedCase]:
        query_embedding = self._model.encode(
            [query],
            normalize_embeddings=self._normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0].astype(np.float32)

        if self._normalize:
            scores = self._case_embeddings @ query_embedding
        else:
            doc_norm = np.linalg.norm(self._case_embeddings, axis=1)
            q_norm = np.linalg.norm(query_embedding)
            denominator = np.maximum(doc_norm * q_norm, 1e-12)
            scores = (self._case_embeddings @ query_embedding) / denominator

        ranked = sorted(
            (
                RankedCase(case_id, float(score))
                for case_id, score in zip(self._case_ids, scores, strict=True)
            ),
            key=lambda x: (-x.score, x.case_id),
        )
        return ranked if top_k is None else ranked[:top_k]


class BGEM3DenseRetriever(DenseRetriever):
    """기존 Runner와의 호환성을 위한 AXCase 입력 wrapper."""

    def __init__(
        self,
        cases: Sequence[AXCase],
        model_name: str = "BAAI/bge-m3",
        normalize_embeddings: bool = True,
        device: str | None = None,
    ) -> None:
        documents = {case.case_id: case.problem_view_text() for case in cases}
        super().__init__(
            documents,
            model_name=model_name,
            normalize_embeddings=normalize_embeddings,
            device=device,
        )
