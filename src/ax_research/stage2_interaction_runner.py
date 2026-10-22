"""Stage 2-4 Query-Case Interaction experiment.

Professor-proposed interaction:
    [q, c, q*c, |q-c|] -> MLP -> relevance score

Hybrid candidate provenance from Stage 2-3 is replayed exactly.
Evaluation uses Leave-One-Query-Out to prevent the held-out query's Gold labels
from entering training.
"""

from __future__ import annotations

import csv
import random
from collections import OrderedDict, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

from .config import RQ1Config
from .data import AXCase, GoldRecord, RelevanceLabel, index_by
from .evaluation import build_perspective_gold, evaluate_at_k, gold_delta_at_k
from .selection import branch_balanced_unique


@dataclass(frozen=True)
class Candidate:
    case_id: str
    source: str
    dense_rank: int | None
    sparse_rank: int | None


@dataclass(frozen=True)
class BranchCandidates:
    query_id: str
    run_id: int
    perspective_id: str
    leg_k: int
    candidates: tuple[Candidate, ...]


class QueryCaseMLP(nn.Module):
    def __init__(self, projection_dim: int, hidden_dim: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(projection_dim * 4, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, interaction: torch.Tensor) -> torch.Tensor:
        return self.net(interaction).squeeze(-1)


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_hybrid_candidates(
    path: str | Path,
) -> OrderedDict[tuple[str, int, str, int], BranchCandidates]:
    grouped: OrderedDict[
        tuple[str, int, str, int], list[Candidate]
    ] = OrderedDict()

    for row in _read_csv(path):
        key = (
            row["query_id"],
            int(row["run_id"]),
            row["perspective_id"],
            int(row["leg_k"]),
        )
        dense_rank = int(row["dense_rank"]) if row["dense_rank"] else None
        sparse_rank = int(row["sparse_rank"]) if row["sparse_rank"] else None
        grouped.setdefault(key, []).append(
            Candidate(
                case_id=row["case_id"],
                source=row["source"],
                dense_rank=dense_rank,
                sparse_rank=sparse_rank,
            )
        )

    result: OrderedDict[
        tuple[str, int, str, int], BranchCandidates
    ] = OrderedDict()
    for key, candidates in grouped.items():
        if len({c.case_id for c in candidates}) != len(candidates):
            raise ValueError(f"Duplicate candidate in branch {key}")
        result[key] = BranchCandidates(
            query_id=key[0],
            run_id=key[1],
            perspective_id=key[2],
            leg_k=key[3],
            candidates=tuple(candidates),
        )

    if not result:
        raise ValueError(f"No hybrid candidates found: {path}")
    return result


def load_branch_query_texts(
    stage2_equal_branch_csv: str | Path,
) -> dict[tuple[str, int, str], str]:
    result: dict[tuple[str, int, str], str] = {}
    for row in _read_csv(stage2_equal_branch_csv):
        key = (row["query_id"], int(row["run_id"]), row["perspective_id"])
        text = row["branch_query_text"]
        existing = result.get(key)
        if existing is not None and existing != text:
            raise ValueError(f"Inconsistent branch query text for {key}")
        result[key] = text
    return result


def rrf_score(candidate: Candidate, constant: int = 60) -> float:
    score = 0.0
    if candidate.dense_rank is not None:
        score += 1.0 / (constant + candidate.dense_rank)
    if candidate.sparse_rank is not None:
        score += 1.0 / (constant + candidate.sparse_rank)
    return score


def fit_case_pca(
    case_vectors: np.ndarray,
    projection_dim: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit unlabeled PCA basis using corpus Case vectors only."""

    if case_vectors.ndim != 2:
        raise ValueError("case_vectors must be a matrix")
    if projection_dim <= 0 or projection_dim > min(case_vectors.shape):
        raise ValueError("invalid projection_dim")

    mean = case_vectors.mean(axis=0, keepdims=True)
    centered = case_vectors - mean
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    basis = vh[:projection_dim].T.astype(np.float32)
    return mean[0].astype(np.float32), basis


def project(
    vectors: np.ndarray,
    mean: np.ndarray,
    basis: np.ndarray,
) -> np.ndarray:
    return ((vectors - mean) @ basis).astype(np.float32)


def interaction_features(
    q: torch.Tensor,
    cases: torch.Tensor,
) -> torch.Tensor:
    if q.ndim != 1 or cases.ndim != 2:
        raise ValueError("q must be 1D and cases must be 2D")
    if cases.shape[1] != q.shape[0]:
        raise ValueError("q/c dimension mismatch")
    q_rows = q.unsqueeze(0).expand(cases.shape[0], -1)
    return torch.cat(
        [q_rows, cases, q_rows * cases, torch.abs(q_rows - cases)],
        dim=1,
    )


def encode_interaction_space(
    *,
    cases: Sequence[AXCase],
    branch_query_texts: Mapping[tuple[str, int, str], str],
    model_name: str,
    projection_dim: int,
) -> tuple[
    dict[str, np.ndarray],
    dict[tuple[str, int, str], np.ndarray],
]:
    """Encode case equal-mean multi-view and branch queries, then corpus-PCA project."""

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    problem = model.encode(
        [f"[PROBLEM] {case.business_problem}" for case in cases],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    ).astype(np.float32)
    task = model.encode(
        [f"[TASK] {case.ax_target_task}" for case in cases],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    ).astype(np.float32)
    context = model.encode(
        [f"[CONTEXT] {case.business_context}" for case in cases],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    ).astype(np.float32)

    case_raw = (problem + task + context) / 3.0
    mean, basis = fit_case_pca(case_raw, projection_dim)
    case_projected = project(case_raw, mean, basis)

    query_keys = list(branch_query_texts)
    query_raw = model.encode(
        [branch_query_texts[key] for key in query_keys],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    ).astype(np.float32)
    query_projected = project(query_raw, mean, basis)

    case_map = {
        case.case_id: case_projected[index]
        for index, case in enumerate(cases)
    }
    query_map = {
        key: query_projected[index]
        for index, key in enumerate(query_keys)
    }
    return case_map, query_map


def _branch_pairwise_loss(
    model: QueryCaseMLP,
    *,
    query_vector: np.ndarray,
    candidate_vectors: np.ndarray,
    positive_mask: np.ndarray,
    pairwise_scale: float,
) -> torch.Tensor | None:
    positives = int(positive_mask.sum())
    negatives = int((~positive_mask).sum())
    if positives == 0 or negatives == 0:
        return None

    features = interaction_features(
        torch.tensor(query_vector, dtype=torch.float32),
        torch.tensor(candidate_vectors, dtype=torch.float32),
    )
    scores = model(features)
    mask = torch.tensor(positive_mask, dtype=torch.bool)
    pos = scores[mask]
    neg = scores[~mask]
    difference = pos[:, None] - neg[None, :]
    return F.softplus(-pairwise_scale * difference).mean()


def train_interaction_for_holdout(
    *,
    holdout_query_id: str,
    leg_k: int,
    branches: Mapping[tuple[str, int, str, int], BranchCandidates],
    query_vectors: Mapping[tuple[str, int, str], np.ndarray],
    case_vectors: Mapping[str, np.ndarray],
    gold_records: Sequence[GoldRecord],
    projection_dim: int,
    hidden_dim: int,
    dropout: float,
    seed: int,
    learning_rate: float,
    weight_decay: float,
    epochs: int,
    pairwise_scale: float,
) -> QueryCaseMLP:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    model = QueryCaseMLP(projection_dim, hidden_dim, dropout)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay,
    )
    gold_index = index_by(gold_records, "query_id")

    by_query: dict[str, list[tuple[str, int, str, int]]] = defaultdict(list)
    for key in branches:
        if key[3] == leg_k and key[0] != holdout_query_id:
            by_query[key[0]].append(key)

    if not by_query:
        raise ValueError("No training queries for interaction model")

    for _ in range(epochs):
        model.train()
        query_losses: list[torch.Tensor] = []

        for query_id, keys in sorted(by_query.items()):
            gold = set(gold_index[query_id].gold_relevant_cases)
            branch_losses: list[torch.Tensor] = []

            for key in keys:
                branch = branches[key]
                ids = [candidate.case_id for candidate in branch.candidates]
                vectors = np.stack([case_vectors[cid] for cid in ids])
                positive_mask = np.asarray(
                    [cid in gold for cid in ids], dtype=bool
                )
                loss = _branch_pairwise_loss(
                    model,
                    query_vector=query_vectors[key[:3]],
                    candidate_vectors=vectors,
                    positive_mask=positive_mask,
                    pairwise_scale=pairwise_scale,
                )
                if loss is not None:
                    branch_losses.append(loss)

            if branch_losses:
                query_losses.append(torch.stack(branch_losses).mean())

        if not query_losses:
            raise ValueError("No valid pairwise training branches")

        loss = torch.stack(query_losses).mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    return model


def _evaluate_final(
    *,
    final_ids: Sequence[str],
    query_id: str,
    k_values: Sequence[int],
    labels: Sequence[RelevanceLabel],
    gold_index: Mapping[str, GoldRecord],
    case_index: Mapping[str, AXCase],
    gold_threshold: int,
) -> list[dict[str, float | int]]:
    gold = gold_index[query_id]
    perspective_gold = build_perspective_gold(
        labels,
        query_id=query_id,
        threshold=gold_threshold,
    )
    rows: list[dict[str, float | int]] = []
    for k in k_values:
        metrics = evaluate_at_k(
            ranked_case_ids=final_ids,
            gold_case_ids=gold.gold_relevant_cases,
            perspective_gold=perspective_gold,
            case_index=case_index,
            gold_strategies=gold.gold_strategy_set,
            k=k,
        )
        rows.append(asdict(metrics))
    return rows


def run_stage2_interaction_loqo(
    *,
    experiment_id: str,
    rq1_config: RQ1Config,
    cases: Sequence[AXCase],
    labels: Sequence[RelevanceLabel],
    gold_records: Sequence[GoldRecord],
    hybrid_candidate_csv: str | Path,
    stage2_equal_branch_csv: str | Path,
    leg_k_values: Sequence[int],
    model_name: str,
    projection_dim: int,
    hidden_dim: int,
    dropout: float,
    seed: int,
    learning_rate: float,
    weight_decay: float,
    epochs: int,
    pairwise_scale: float,
    rrf_constant: int,
    output_dir: str | Path,
) -> tuple[Path, Path, Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    branches = load_hybrid_candidates(hybrid_candidate_csv)
    branch_query_texts = load_branch_query_texts(stage2_equal_branch_csv)
    case_vectors, query_vectors = encode_interaction_space(
        cases=cases,
        branch_query_texts=branch_query_texts,
        model_name=model_name,
        projection_dim=projection_dim,
    )

    gold_index = index_by(gold_records, "query_id")
    case_index = index_by(cases, "case_id")

    ranking_rows: list[dict[str, object]] = []
    final_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []
    delta_rows: list[dict[str, object]] = []

    for leg_k in leg_k_values:
        for fold_index, holdout_query_id in enumerate(rq1_config.query_ids):
            model = train_interaction_for_holdout(
                holdout_query_id=holdout_query_id,
                leg_k=leg_k,
                branches=branches,
                query_vectors=query_vectors,
                case_vectors=case_vectors,
                gold_records=gold_records,
                projection_dim=projection_dim,
                hidden_dim=hidden_dim,
                dropout=dropout,
                seed=seed + fold_index + leg_k * 100,
                learning_rate=learning_rate,
                weight_decay=weight_decay,
                epochs=epochs,
                pairwise_scale=pairwise_scale,
            )
            model.eval()

            for run_id in range(1, rq1_config.llm_repeats + 1):
                qci_rankings: OrderedDict[str, list[str]] = OrderedDict()
                rrf_rankings: OrderedDict[str, list[str]] = OrderedDict()

                branch_keys = [
                    key for key in branches
                    if key[0] == holdout_query_id
                    and key[1] == run_id
                    and key[3] == leg_k
                ]
                if not branch_keys:
                    raise KeyError(
                        f"Missing hybrid branches for {(holdout_query_id, run_id, leg_k)}"
                    )

                for key in branch_keys:
                    branch = branches[key]
                    ids = [candidate.case_id for candidate in branch.candidates]
                    vectors = np.stack([case_vectors[cid] for cid in ids])
                    features = interaction_features(
                        torch.tensor(query_vectors[key[:3]], dtype=torch.float32),
                        torch.tensor(vectors, dtype=torch.float32),
                    )
                    with torch.no_grad():
                        qci_scores = model(features).cpu().numpy()

                    qci_order = sorted(
                        range(len(ids)),
                        key=lambda i: (-float(qci_scores[i]), ids[i]),
                    )
                    rrf_scores = [
                        rrf_score(candidate, rrf_constant)
                        for candidate in branch.candidates
                    ]
                    rrf_order = sorted(
                        range(len(ids)),
                        key=lambda i: (-float(rrf_scores[i]), ids[i]),
                    )

                    qci_rankings[branch.perspective_id] = [
                        ids[i] for i in qci_order
                    ]
                    rrf_rankings[branch.perspective_id] = [
                        ids[i] for i in rrf_order
                    ]

                    for rank, i in enumerate(qci_order, start=1):
                        candidate = branch.candidates[i]
                        ranking_rows.append(
                            {
                                "experiment_id": experiment_id,
                                "system": "stage2_query_case_interaction",
                                "leg_k": leg_k,
                                "query_id": holdout_query_id,
                                "run_id": run_id,
                                "perspective_id": branch.perspective_id,
                                "rank": rank,
                                "case_id": candidate.case_id,
                                "source": candidate.source,
                                "dense_rank": candidate.dense_rank or "",
                                "sparse_rank": candidate.sparse_rank or "",
                                "score": float(qci_scores[i]),
                            }
                        )

                max_k = max(rq1_config.evaluation_k)
                qci_selected = branch_balanced_unique(
                    qci_rankings, k=max_k
                )
                rrf_selected = branch_balanced_unique(
                    rrf_rankings, k=max_k
                )
                qci_final = [cid for _, cid in qci_selected]
                rrf_final = [cid for _, cid in rrf_selected]

                for system, selected in (
                    ("stage2_query_case_interaction", qci_selected),
                    ("stage2_same_pool_rrf", rrf_selected),
                ):
                    for final_rank, (pid, cid) in enumerate(selected, start=1):
                        final_rows.append(
                            {
                                "experiment_id": experiment_id,
                                "system": system,
                                "leg_k": leg_k,
                                "query_id": holdout_query_id,
                                "run_id": run_id,
                                "final_rank": final_rank,
                                "source_perspective_id": pid,
                                "case_id": cid,
                            }
                        )

                for system, final_ids in (
                    ("stage2_query_case_interaction", qci_final),
                    ("stage2_same_pool_rrf", rrf_final),
                ):
                    for metrics in _evaluate_final(
                        final_ids=final_ids,
                        query_id=holdout_query_id,
                        k_values=rq1_config.evaluation_k,
                        labels=labels,
                        gold_index=gold_index,
                        case_index=case_index,
                        gold_threshold=rq1_config.gold_threshold,
                    ):
                        metric_rows.append(
                            {
                                "experiment_id": experiment_id,
                                "system": system,
                                "leg_k": leg_k,
                                "run_id": run_id,
                                "query_id": holdout_query_id,
                                **metrics,
                                "branch_count": len(branch_keys),
                                "final_unique_count": len(final_ids),
                            }
                        )

                gold_ids = gold_index[
                    holdout_query_id
                ].gold_relevant_cases
                for k in rq1_config.evaluation_k:
                    delta = gold_delta_at_k(
                        rrf_final,
                        qci_final,
                        gold_ids,
                        k,
                    )
                    delta_rows.append(
                        {
                            "query_id": holdout_query_id,
                            "run_id": run_id,
                            "leg_k": leg_k,
                            "k": k,
                            "gained_gold_count": len(delta.gained),
                            "lost_gold_count": len(delta.lost),
                            "net_gold_change": delta.net,
                            "gained_gold_cases": "|".join(sorted(delta.gained)),
                            "lost_gold_cases": "|".join(sorted(delta.lost)),
                        }
                    )

    rankings_path = output / "stage2_interaction_branch_rankings.csv"
    final_path = output / "stage2_interaction_final_rankings.csv"
    metrics_path = output / "stage2_interaction_metrics.csv"
    delta_path = output / "stage2_interaction_gold_delta_vs_rrf.csv"
    _write_csv(rankings_path, ranking_rows)
    _write_csv(final_path, final_rows)
    _write_csv(metrics_path, metric_rows)
    _write_csv(delta_path, delta_rows)
    return rankings_path, final_path, metrics_path, delta_path


def summarize_stage2_interaction(
    metrics_csv: str | Path,
    output_csv: str | Path,
) -> Path:
    rows = _read_csv(metrics_csv)
    grouped: dict[tuple[str, int, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["system"], int(row["leg_k"]), int(row["k"]))].append(row)

    output_rows: list[dict[str, object]] = []
    for (system, leg_k, k), items in sorted(grouped.items()):
        recall = [float(row["recall"]) for row in items]
        perspective = [float(row["perspective_coverage"]) for row in items]
        strategy = [float(row["strategy_coverage"]) for row in items]
        output_rows.append(
            {
                "system": system,
                "leg_k": leg_k,
                "k": k,
                "row_count": len(items),
                "mean_recall": sum(recall) / len(recall),
                "mean_perspective_coverage": sum(perspective) / len(perspective),
                "mean_strategy_coverage": sum(strategy) / len(strategy),
            }
        )

    output = Path(output_csv)
    _write_csv(output, output_rows)
    return output
