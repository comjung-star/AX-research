"""Stage 2-2 Query-Conditioned Gated Fusion runner."""

from __future__ import annotations

import csv
import random
from collections import OrderedDict, defaultdict
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

from .config import RQ1Config
from .data import AXCase, GoldRecord, RelevanceLabel, index_by
from .evaluation import build_perspective_gold, evaluate_at_k
from .selection import branch_balanced_unique

VIEW_NAMES = ("business_problem", "ax_target_task", "business_context")


@dataclass(frozen=True)
class BranchScores:
    query_id: str
    run_id: int
    perspective_id: str
    perspective_title: str
    perspective_description: str
    branch_query_text: str
    case_ids: tuple[str, ...]
    view_scores: np.ndarray


class TinyQueryConditionedGate(nn.Module):
    """3 anchor similarities -> 3 softmax view weights."""

    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(3, 3)
        nn.init.zeros_(self.linear.weight)
        nn.init.zeros_(self.linear.bias)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.linear(features), dim=-1)


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


def load_stage2_equal_branch_scores(
    path: str | Path,
) -> OrderedDict[tuple[str, int, str], BranchScores]:
    grouped: OrderedDict[tuple[str, int, str], list[dict[str, str]]] = OrderedDict()
    for row in _read_csv(path):
        key = (row["query_id"], int(row["run_id"]), row["perspective_id"])
        grouped.setdefault(key, []).append(row)

    result: OrderedDict[tuple[str, int, str], BranchScores] = OrderedDict()
    for key, rows in grouped.items():
        first = rows[0]
        case_ids = tuple(row["case_id"] for row in rows)
        if len(case_ids) != len(set(case_ids)):
            raise ValueError(f"Duplicate case rows in branch {key}")
        scores = np.asarray(
            [[float(row["problem_score"]), float(row["task_score"]), float(row["context_score"])] for row in rows],
            dtype=np.float32,
        )
        result[key] = BranchScores(
            query_id=key[0],
            run_id=key[1],
            perspective_id=key[2],
            perspective_title=first["perspective_title"],
            perspective_description=first["perspective_description"],
            branch_query_text=first["branch_query_text"],
            case_ids=case_ids,
            view_scores=scores,
        )
    if not result:
        raise ValueError(f"No Stage 2-1 branch scores found: {path}")
    return result


def compute_anchor_features(
    branches: Mapping[tuple[str, int, str], BranchScores],
    *,
    model_name: str,
    anchors: Mapping[str, str],
) -> dict[tuple[str, int, str], np.ndarray]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    keys = list(branches)
    query_texts = [branches[key].branch_query_text for key in keys]
    anchor_texts = [anchors[name] for name in VIEW_NAMES]
    embeddings = model.encode(
        query_texts + anchor_texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    ).astype(np.float32)
    query_embeddings = embeddings[: len(query_texts)]
    anchor_embeddings = embeddings[len(query_texts):]
    feature_matrix = query_embeddings @ anchor_embeddings.T
    return {key: feature_matrix[i] for i, key in enumerate(keys)}


def _branch_loss(
    gate: TinyQueryConditionedGate,
    *,
    feature: torch.Tensor,
    view_scores: torch.Tensor,
    positive_mask: torch.Tensor,
    pairwise_scale: float,
) -> torch.Tensor:
    weights = gate(feature)
    scores = view_scores @ weights
    positive = scores[positive_mask]
    negative = scores[~positive_mask]
    if positive.numel() == 0 or negative.numel() == 0:
        raise ValueError("Each training branch needs positive and negative cases")
    difference = positive[:, None] - negative[None, :]
    return F.softplus(-pairwise_scale * difference).mean()


def train_gate_for_holdout(
    *,
    holdout_query_id: str,
    branches: Mapping[tuple[str, int, str], BranchScores],
    features: Mapping[tuple[str, int, str], np.ndarray],
    gold_records: Sequence[GoldRecord],
    seed: int,
    learning_rate: float,
    weight_decay: float,
    epochs: int,
    pairwise_scale: float,
) -> TinyQueryConditionedGate:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    gold_index = index_by(gold_records, "query_id")
    gate = TinyQueryConditionedGate()
    optimizer = torch.optim.AdamW(gate.parameters(), lr=learning_rate, weight_decay=weight_decay)

    by_query: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    for key in branches:
        if key[0] != holdout_query_id:
            by_query[key[0]].append(key)

    for _ in range(epochs):
        query_losses: list[torch.Tensor] = []
        for query_id, keys in by_query.items():
            gold = set(gold_index[query_id].gold_relevant_cases)
            branch_losses: list[torch.Tensor] = []
            for key in keys:
                branch = branches[key]
                positive_mask = torch.tensor(
                    [case_id in gold for case_id in branch.case_ids],
                    dtype=torch.bool,
                )
                branch_losses.append(
                    _branch_loss(
                        gate,
                        feature=torch.tensor(features[key], dtype=torch.float32),
                        view_scores=torch.tensor(branch.view_scores, dtype=torch.float32),
                        positive_mask=positive_mask,
                        pairwise_scale=pairwise_scale,
                    )
                )
            query_losses.append(torch.stack(branch_losses).mean())

        loss = torch.stack(query_losses).mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    return gate


def _jaccard(left: Sequence[str], right: Sequence[str]) -> float:
    a, b = set(left), set(right)
    union = a | b
    return 1.0 if not union else len(a & b) / len(union)


def _duplicate_candidate_rate(
    branch_rankings: Mapping[str, Sequence[str]], local_k: int
) -> float:
    flattened = [cid for ranking in branch_rankings.values() for cid in ranking[:local_k]]
    if not flattened:
        return 0.0
    return 1.0 - len(set(flattened)) / len(flattened)


def run_stage2_gated_loqo(
    *,
    experiment_id: str,
    rq1_config: RQ1Config,
    cases: Sequence[AXCase],
    labels: Sequence[RelevanceLabel],
    gold_records: Sequence[GoldRecord],
    stage2_equal_branch_csv: str | Path,
    model_name: str,
    anchors: Mapping[str, str],
    seed: int,
    learning_rate: float,
    weight_decay: float,
    epochs: int,
    pairwise_scale: float,
    output_dir: str | Path,
    system_name: str = "stage2_query_conditioned_gated_dense",
) -> tuple[Path, Path, Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    branches = load_stage2_equal_branch_scores(stage2_equal_branch_csv)
    features = compute_anchor_features(branches, model_name=model_name, anchors=anchors)
    gold_index = index_by(gold_records, "query_id")
    case_index = index_by(cases, "case_id")
    max_k = max(rq1_config.evaluation_k)

    weight_rows: list[dict[str, object]] = []
    branch_rows: list[dict[str, object]] = []
    final_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []

    for fold_index, holdout_query_id in enumerate(rq1_config.query_ids):
        gate = train_gate_for_holdout(
            holdout_query_id=holdout_query_id,
            branches=branches,
            features=features,
            gold_records=gold_records,
            seed=seed + fold_index,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            epochs=epochs,
            pairwise_scale=pairwise_scale,
        )
        perspective_gold = build_perspective_gold(
            labels, query_id=holdout_query_id, threshold=rq1_config.gold_threshold
        )
        gold = gold_index[holdout_query_id]

        for run_id in range(1, rq1_config.llm_repeats + 1):
            branch_keys = [key for key in branches if key[0] == holdout_query_id and key[1] == run_id]
            if not branch_keys:
                raise KeyError(f"Missing branch scores for {(holdout_query_id, run_id)}")
            branch_rankings: OrderedDict[str, list[str]] = OrderedDict()

            for key in branch_keys:
                branch = branches[key]
                with torch.no_grad():
                    weights = gate(torch.tensor(features[key], dtype=torch.float32)).cpu().numpy().astype(np.float32)
                fused = branch.view_scores @ weights
                order = np.argsort(-fused, kind="stable")
                ranked_ids = [branch.case_ids[i] for i in order]
                branch_rankings[branch.perspective_id] = ranked_ids

                weight_rows.append({
                    "experiment_id": experiment_id,
                    "system": system_name,
                    "holdout_query_id": holdout_query_id,
                    "run_id": run_id,
                    "perspective_id": branch.perspective_id,
                    "problem_anchor_similarity": float(features[key][0]),
                    "task_anchor_similarity": float(features[key][1]),
                    "context_anchor_similarity": float(features[key][2]),
                    "problem_weight": float(weights[0]),
                    "task_weight": float(weights[1]),
                    "context_weight": float(weights[2]),
                })

                for local_rank, i in enumerate(order, start=1):
                    branch_rows.append({
                        "experiment_id": experiment_id,
                        "system": system_name,
                        "run_id": run_id,
                        "query_id": holdout_query_id,
                        "perspective_id": branch.perspective_id,
                        "perspective_title": branch.perspective_title,
                        "perspective_description": branch.perspective_description,
                        "branch_query_text": branch.branch_query_text,
                        "local_rank": local_rank,
                        "case_id": branch.case_ids[i],
                        "score": float(fused[i]),
                        "problem_score": float(branch.view_scores[i, 0]),
                        "task_score": float(branch.view_scores[i, 1]),
                        "context_score": float(branch.view_scores[i, 2]),
                        "problem_weight": float(weights[0]),
                        "task_weight": float(weights[1]),
                        "context_weight": float(weights[2]),
                    })

            selected = branch_balanced_unique(branch_rankings, k=max_k)
            final_ids = [case_id for _, case_id in selected]
            for final_rank, (source_branch, case_id) in enumerate(selected, start=1):
                final_rows.append({
                    "experiment_id": experiment_id,
                    "system": system_name,
                    "run_id": run_id,
                    "query_id": holdout_query_id,
                    "final_rank": final_rank,
                    "source_perspective_id": source_branch,
                    "case_id": case_id,
                })

            local_sets = {pid: ids[:max_k] for pid, ids in branch_rankings.items()}
            pair_scores = [_jaccard(local_sets[a], local_sets[b]) for a, b in combinations(local_sets, 2)]
            mean_jaccard = sum(pair_scores) / len(pair_scores) if pair_scores else 1.0
            duplicate_rate = _duplicate_candidate_rate(branch_rankings, max_k)

            for k in rq1_config.evaluation_k:
                metrics = evaluate_at_k(
                    ranked_case_ids=final_ids,
                    gold_case_ids=gold.gold_relevant_cases,
                    perspective_gold=perspective_gold,
                    case_index=case_index,
                    gold_strategies=gold.gold_strategy_set,
                    k=k,
                )
                metric_rows.append({
                    "experiment_id": experiment_id,
                    "system": system_name,
                    "run_id": run_id,
                    "query_id": holdout_query_id,
                    **asdict(metrics),
                    "generated_perspective_count": len(branch_keys),
                    "mean_branch_jaccard_at_max_k": mean_jaccard,
                    "duplicate_candidate_rate_at_max_k": duplicate_rate,
                })

    weight_path = output / f"{system_name}_weights.csv"
    branch_path = output / f"{system_name}_branch_rankings.csv"
    final_path = output / f"{system_name}_final_rankings.csv"
    metrics_path = output / f"{system_name}_metrics.csv"
    _write_csv(weight_path, weight_rows)
    _write_csv(branch_path, branch_rows)
    _write_csv(final_path, final_rows)
    _write_csv(metrics_path, metric_rows)
    return weight_path, branch_path, final_path, metrics_path
