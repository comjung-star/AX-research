"""Stage 2-1 Multi-view Dense Retrieval.

AX Case의 Problem / Task / Context를 각각 BGE-M3로 임베딩하고,
각 View와 branch query의 cosine similarity를 계산한 뒤 고정 가중 평균으로
하나의 branch relevance score를 만듭니다.

Stage 2-1에서는 학습형 gate를 사용하지 않습니다. 그것은 Stage 2-2의
독립적인 ablation 대상입니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from ..data import AXCase


@dataclass(frozen=True)
class MultiViewRankedCase:
    case_id: str
    score: float
    problem_score: float
    task_score: float
    context_score: float


def weighted_view_score(
    problem_score: float,
    task_score: float,
    context_score: float,
    weights: Mapping[str, float],
) -> float:
    """세 View score를 정규화된 가중 평균으로 결합합니다."""

    wp = float(weights["business_problem"])
    wt = float(weights["ax_target_task"])
    wc = float(weights["business_context"])
    total = wp + wt + wc
    if total <= 0:
        raise ValueError("Multi-view weights must have a positive sum")
    return (
        problem_score * wp + task_score * wt + context_score * wc
    ) / total


class MultiViewDenseRetriever:
    """Problem / Task / Context를 분리 임베딩하는 BGE-M3 retriever."""

    def __init__(
        self,
        cases: Sequence[AXCase],
        *,
        model_name: str = "BAAI/bge-m3",
        normalize_embeddings: bool = True,
        weights: Mapping[str, float] | None = None,
        device: str | None = None,
    ) -> None:
        if not cases:
            raise ValueError("cases must not be empty")

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Multi-view Dense Retrieval에는 sentence-transformers가 필요합니다."
            ) from exc

        self._cases = list(cases)
        self._case_ids = [case.case_id for case in self._cases]
        self._normalize = normalize_embeddings
        self._weights = dict(
            weights
            or {
                "business_problem": 1.0 / 3.0,
                "ax_target_task": 1.0 / 3.0,
                "business_context": 1.0 / 3.0,
            }
        )
        self._model = SentenceTransformer(model_name, device=device)

        n = len(self._cases)
        texts = (
            [f"[PROBLEM] {case.business_problem}" for case in self._cases]
            + [f"[TASK] {case.ax_target_task}" for case in self._cases]
            + [f"[CONTEXT] {case.business_context}" for case in self._cases]
        )
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).astype(np.float32)

        self._problem_embeddings = embeddings[:n]
        self._task_embeddings = embeddings[n : 2 * n]
        self._context_embeddings = embeddings[2 * n :]

    def _cosine_scores(
        self,
        matrix: np.ndarray,
        query_embedding: np.ndarray,
    ) -> np.ndarray:
        if self._normalize:
            return matrix @ query_embedding

        doc_norm = np.linalg.norm(matrix, axis=1)
        q_norm = np.linalg.norm(query_embedding)
        denominator = np.maximum(doc_norm * q_norm, 1e-12)
        return (matrix @ query_embedding) / denominator

    def search(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[MultiViewRankedCase]:
        query_embedding = self._model.encode(
            [query],
            normalize_embeddings=self._normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0].astype(np.float32)

        problem = self._cosine_scores(self._problem_embeddings, query_embedding)
        task = self._cosine_scores(self._task_embeddings, query_embedding)
        context = self._cosine_scores(self._context_embeddings, query_embedding)

        ranked = [
            MultiViewRankedCase(
                case_id=case_id,
                score=weighted_view_score(
                    float(sp),
                    float(st),
                    float(sc),
                    self._weights,
                ),
                problem_score=float(sp),
                task_score=float(st),
                context_score=float(sc),
            )
            for case_id, sp, st, sc in zip(
                self._case_ids, problem, task, context, strict=True
            )
        ]
        ranked.sort(key=lambda x: (-x.score, x.case_id))
        return ranked if top_k is None else ranked[:top_k]
