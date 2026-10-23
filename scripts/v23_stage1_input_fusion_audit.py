#!/usr/bin/env python3
"""Frozen v2.3 Stage-1 input-vs-fusion factorial replay.

2 factors:
 - Runtime query text: perspective title; title+description; original problem+title+description
 - Branch result fusion: round-robin branch preservation; cross-branch reciprocal-rank fusion
No solution, Ground Truth, reference-perspective title, or evaluator labels enter retrieval.
Uses the exact Stage-1 frozen document/title embeddings and same 97 generated perspectives.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
from collections import Counter, defaultdict, OrderedDict
from pathlib import Path

import numpy as np

from ax_research.selection import branch_balanced_unique

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "experiments/v23_dev/stage1"
OUT = ROOT / "experiments/v23_dev/stage1_input_fusion_audit"
OUT.mkdir(parents=True, exist_ok=True)
KS = (5, 10, 20)
INPUTS = ("TITLE", "TITLE_DESCRIPTION", "ORIGINAL_QUERY_WITH_PERSPECTIVE")
FUSIONS = ("ROUND_ROBIN", "RRF")
SEED = 42


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise AssertionError(f"No data to write: {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


corpus_file = ROOT / "data/v2_3/main_cases_v2_3.json"
q_file = ROOT / "data/v2_3/dev_query_candidates_v2_3.json"
gt_file = ROOT / "data/v2_3/ground_truth/silver_dev_qrels_2520.csv"
perspectives_file = SRC / "generated_runtime_perspectives.json"
embedding_file = SRC / "fixed_bge_m3_embeddings.npz"
old_rank_file = SRC / "rankings_top20.csv"
old_metrics_file = SRC / "metrics_by_query.csv"
old_branch_file = SRC / "branch_rankings.csv"

cases = json.loads(corpus_file.read_text(encoding="utf-8"))["cases"]
queries = json.loads(q_file.read_text(encoding="utf-8"))["queries"]
perspectives = json.loads(perspectives_file.read_text(encoding="utf-8"))
npz = np.load(embedding_file, allow_pickle=False)
ids = npz["case_ids"].tolist()
doc = np.asarray(npz["document_embeddings"], dtype=np.float32)
titles = np.asarray(npz["branch_embeddings"], dtype=np.float32)
keys = npz["branch_keys"].tolist()
assert len(cases) == len(ids) == 84 and len(queries) == 10
assert len(keys) == len(perspectives) == len(set(keys)) == 97
assert len(doc) == 84 and titles.shape == (97, doc.shape[1])
assert set(ids) == {c["case_id"] for c in cases}
index = {c["case_id"]: c for c in cases}
qmap = {q["query_id"]: q["business_problem_query"] for q in queries}
keymap = {f"{p['query_id']}|{p['run_id']}|{p['perspective_id']}": p for p in perspectives}
assert list(keymap) == keys, "Frozen Stage 1 branch embeddings are not aligned with perspectives"
assert all(2 <= sum(p["query_id"] == q and p["run_id"] == run for p in perspectives) <= 5
           for q in qmap for run in (1, 2, 3))
assert len(qmap) == 10

label: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
gt = read_csv(gt_file)
assert len(gt) == 2520
for row in gt:
    assert row["provenance"] == "AI_THREE_PASS_MEDIAN_NOT_HUMAN_GOLD"
    assert 0 <= int(row["relevance_0_4"]) <= 4
    if int(row["relevance_0_4"]) >= 3:
        label[row["query_id"]][row["perspective_id"]].add(row["case_id"])
assert all(q in label for q in qmap)
relevant = {q: set().union(*label[q].values()) for q in qmap}
assert all(relevant[q] for q in qmap)
def eval_metrics(q: str, ranked: list[str], k: int) -> tuple[float, float, float]:
    g = relevant[q]
    active = [positive for positive in label[q].values() if positive]
    top = set(ranked[:k])
    relevant_strategy = {s for cid in g for s in index[cid]["strategy_labels"]}
    found_strategy = {s for cid in top for s in index[cid]["strategy_labels"]}
    return (
        len(top & g) / len(g),
        sum(bool(top & g2) for g2 in active) / len(active),
        len(found_strategy & relevant_strategy) / len(relevant_strategy),
    )


old_rank = read_csv(old_rank_file)
old_metrics = read_csv(old_metrics_file)
old_index = {
    (x["system"], x["query_id"], int(x["run_id"])): []
    for x in old_rank
}
for x in old_rank:
    old_index[(x["system"], x["query_id"], int(x["run_id"]))].append(x["case_id"])
old_metric_index = {
    (x["system"], x["query_id"], int(x["run_id"]), int(x["k"])): x
    for x in old_metrics
}
branch_ranks = defaultdict(list)
for row in read_csv(old_branch_file):
    if row["retrieval"] != "dense":
        continue
    branch_ranks[(row["query_id"], int(row["run_id"]), row["perspective_id"])].append(row["case_id"])
assert len(branch_ranks) == 97
assert all(len(x) == 84 for x in branch_ranks.values())


def sort_dense(vector: np.ndarray) -> list[str]:
    s = doc @ np.asarray(vector, dtype=np.float32)
    return [ids[i] for i in sorted(range(len(ids)), key=lambda i: (-float(s[i]), ids[i]))]


def rr(branches: OrderedDict[str, list[str]], k: int = 84) -> list[str]:
    return [cid for _p, cid in branch_balanced_unique(branches, k=k)]


def rrf(branches: OrderedDict[str, list[str]], k: int = 84) -> list[str]:
    scores = defaultdict(float)
    for rank_list in branches.values():
        for rank, cid in enumerate(rank_list, start=1):
            scores[cid] += 1 / (60 + rank)
    return sorted(ids, key=lambda cid: (-scores[cid], cid))[:k]


# Mandatory exact replay: old title-only branch rankings and final rankings
for i, b in enumerate(perspectives):
    key = (b["query_id"], b["run_id"], b["perspective_id"])
    got = sort_dense(titles[i])
    assert got == branch_ranks[key], f"Existing title-only branch replay mismatch: {key}"
for q in qmap:
    for run in (1, 2, 3):
        br = OrderedDict(
            (p["perspective_id"], branch_ranks[(q, run, p["perspective_id"])])
            for p in perspectives if p["query_id"] == q and p["run_id"] == run
        )
        old = old_index[("mp_dense_bge_m3", q, run)]
        got = rr(br)[:20]
        assert got == old, f"Existing title-only output replay mismatch: {q}/{run}"
        for k in KS:
            original = old_metric_index[("mp_dense_bge_m3", q, run, k)]
            calc = eval_metrics(q, got, k)
            assert abs(calc[0] - float(original["recall"])) < 1e-10
            assert abs(calc[1] - float(original["perspective_coverage"])) < 1e-10
            assert abs(calc[2] - float(original["strategy_coverage"])) < 1e-10
print("PASS: exact 97 branch rankings, 30 final rankings, all metrics replayed from frozen Stage 1", flush=True)


# NEW vectors are generated for the input intervention only.
def make_input(p: dict[str, object], variant: str) -> str:
    title = str(p["perspective_title"]).strip()
    description = str(p["perspective_description"]).strip()
    if variant == "TITLE":
        return title
    if variant == "TITLE_DESCRIPTION":
        return f"[PERSPECTIVE] {title}\n[DESCRIPTION] {description}"
    if variant == "ORIGINAL_QUERY_WITH_PERSPECTIVE":
        return (f"[BUSINESS PROBLEM] {qmap[str(p['query_id'])]}\n"
                f"[PERSPECTIVE] {title}\n[DESCRIPTION] {description}")
    raise ValueError(variant)


from sentence_transformers import SentenceTransformer
print("Encoding only new query variants with same BAAI/bge-m3", flush=True)
model = SentenceTransformer("BAAI/bge-m3", device="cpu")
vectors = {"TITLE": titles}
for variant in INPUTS[1:]:
    vectors[variant] = model.encode(
        [make_input(p, variant) for p in perspectives],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
        batch_size=16,
    ).astype(np.float32)
    assert vectors[variant].shape == titles.shape
    assert np.isfinite(vectors[variant]).all()

# Keep all six variants, not the winner only.
metric_rows: list[dict[str, object]] = []
ranking_rows: list[dict[str, object]] = []
run_rows: list[dict[str, object]] = []
input_rows: list[dict[str, object]] = []
for i, p in enumerate(perspectives):
    key = keys[i]
    for variant in INPUTS:
        txt = make_input(p, variant)
        input_rows.append(dict(
            query_id=p["query_id"], run_id=p["run_id"], perspective_id=p["perspective_id"],
            variant=variant,characters=len(txt),description_chars=len(p["perspective_description"]),
            sha256=hashlib.sha256(txt.encode("utf-8")).hexdigest(),
        ))

for q in qmap:
    for run in (1, 2, 3):
        branch_indices = [
            i for i, p in enumerate(perspectives)
            if p["query_id"] == q and p["run_id"] == run
        ]
        pids = [perspectives[i]["perspective_id"] for i in branch_indices]
        assert len(pids) == len(set(pids))
        original = old_index[("mp_dense_bge_m3", q, run)]
        for variant in INPUTS:
            br = OrderedDict(
                (perspectives[i]["perspective_id"], sort_dense(vectors[variant][i]))
                for i in branch_indices
            )
            for fusion in FUSIONS:
                final = rr(br) if fusion == "ROUND_ROBIN" else rrf(br)
                assert len(final) == len(set(final)) == len(ids)
                assert set(final) == set(ids)
                old_hits = set(original[:10]) & relevant[q]
                new_hits = set(final[:10]) & relevant[q]
                run_rows.append(dict(
                    query_id=q, run_id=run, input_variant=variant, fusion=fusion,
                    branch_count=len(pids),
                    gained_vs_original_top10=len(new_hits - old_hits),
                    lost_vs_original_top10=len(old_hits - new_hits),
                    net_vs_original_top10=len(new_hits) - len(old_hits),
                    original_top10_relevant=len(old_hits),
                    revised_top10_relevant=len(new_hits),
                    same_top10_cases=len(set(original[:10]) & set(final[:10])),
                    branch_overlap_top10_mean=float(np.mean([
                        len(set(br[a][:10]) & set(br[b][:10])) / 10
                        for i, a in enumerate(pids) for b in pids[i + 1:]
                    ])),
                ))
                for k in KS:
                    rec, cov, strat = eval_metrics(q, final, k)
                    metric_rows.append(dict(
                        query_id=q, run_id=run, input_variant=variant,
                        fusion=fusion, k=k, recall=rec,
                        perspective_coverage=cov, strategy_coverage=strat,
                        n_relevant=len(relevant[q]),
                        n_active_reference_views=sum(bool(v) for v in label[q].values()),
                        not_independent_human_gold=True
                    ))
                for rank, cid in enumerate(final[:20], start=1):
                    ranking_rows.append(dict(query_id=q, run_id=run, input_variant=variant,
                        fusion=fusion, rank=rank, case_id=cid,
                        retrieval_source_perspectives="|".join(
                            pid for pid in pids if cid in br[pid][:20]
                        ),
                    ))

assert len(metric_rows) == 30 * len(INPUTS) * len(FUSIONS) * len(KS)
assert len(run_rows) == 30 * 6
write_csv(OUT / "input_text_audit.csv", input_rows)
write_csv(OUT / "replayed_rankings_top20.csv", ranking_rows)
write_csv(OUT / "metrics_by_query_and_run.csv", metric_rows)
write_csv(OUT / "top10_gain_loss_vs_original.csv", run_rows)


# Question-level means first, then average 10 question values: avoids pseudo-replicating runs.
query_rows: list[dict[str, object]] = []
summary_rows: list[dict[str, object]] = []
for variant in INPUTS:
    for fusion in FUSIONS:
        for k in KS:
            query_scores = []
            for q in qmap:
                x = [r for r in metric_rows
                     if r["query_id"] == q and r["input_variant"] == variant
                     and r["fusion"] == fusion and r["k"] == k]
                assert len(x) == 3
                item = dict(
                    query_id=q, input_variant=variant, fusion=fusion, k=k,
                    recall_mean=float(np.mean([r["recall"] for r in x])),
                    perspective_coverage_mean=float(np.mean([r["perspective_coverage"] for r in x])),
                    strategy_coverage_mean=float(np.mean([r["strategy_coverage"] for r in x]))
                )
                query_rows.append(item)
                query_scores.append(item)
            summary_rows.append(dict(
                input_variant=variant, fusion=fusion, k=k,
                unique_dev_queries=10, repeated_runs=30,
                recall_mean=float(np.mean([x["recall_mean"] for x in query_scores])),
                perspective_coverage_mean=float(np.mean([x["perspective_coverage_mean"] for x in query_scores])),
                strategy_coverage_mean=float(np.mean([x["strategy_coverage_mean"] for x in query_scores]))
            ))
write_csv(OUT / "query_level_means.csv", query_rows)
write_csv(OUT / "factorial_summary.csv", summary_rows)


# Factorial main effects; report contrasts, including losses, for each question.
baseline = {(r["query_id"], r["input_variant"], r["fusion"]): r["recall_mean"]
            for r in query_rows if r["k"] == 10}
contrast_rows = []
rng = np.random.default_rng(SEED)
contrasts = [
    ("INPUT_TITLE_DESCRIPTION_VS_TITLE_AT_RR", "TITLE_DESCRIPTION", "ROUND_ROBIN", "TITLE", "ROUND_ROBIN"),
    ("INPUT_ORIGINAL_PLUS_PERSPECTIVE_VS_TITLE_AT_RR", "ORIGINAL_QUERY_WITH_PERSPECTIVE", "ROUND_ROBIN", "TITLE", "ROUND_ROBIN"),
    ("FUSION_RRF_VS_RR_AT_TITLE", "TITLE", "RRF", "TITLE", "ROUND_ROBIN"),
    ("FUSION_RRF_VS_RR_AT_TITLE_DESCRIPTION", "TITLE_DESCRIPTION", "RRF", "TITLE_DESCRIPTION", "ROUND_ROBIN"),
    ("FUSION_RRF_VS_RR_AT_ORIGINAL_PLUS_PERSPECTIVE", "ORIGINAL_QUERY_WITH_PERSPECTIVE", "RRF", "ORIGINAL_QUERY_WITH_PERSPECTIVE", "ROUND_ROBIN"),
    ("JOINT_TITLE_DESCRIPTION_RRF_VS_ORIGINAL", "TITLE_DESCRIPTION", "RRF", "TITLE", "ROUND_ROBIN"),
    ("JOINT_ORIGINAL_PLUS_PERSPECTIVE_RRF_VS_ORIGINAL", "ORIGINAL_QUERY_WITH_PERSPECTIVE", "RRF", "TITLE", "ROUND_ROBIN"),
]
for name, na, fa, nb, fb in contrasts:
    d = np.asarray([baseline[(q, na, fa)] - baseline[(q, nb, fb)] for q in qmap], dtype=float)
    sample = rng.integers(0, len(d), size=(10000, len(d)))
    ci = np.quantile(d[sample].mean(axis=1), [0.025, 0.975])
    contrast_rows.append(dict(
        contrast=name, reference=f"{nb}+{fb}", changed=f"{na}+{fa}",
        recall10_delta_mean=float(np.mean(d)), ci95_query_bootstrap_low=float(ci[0]),
        ci95_query_bootstrap_high=float(ci[1]),
        queries_improved=int(np.sum(d > 1e-9)),
        queries_declined=int(np.sum(d < -1e-9)),
        queries_tied=int(np.sum(np.abs(d) <= 1e-9)),
        bootstrap_resamples=10000,
        inference_note="EXPLORATORY_DEV_PAIRED_QUERY_BOOTSTRAP_NOT_HELD_OUT"
    ))
write_csv(OUT / "paired_contrasts_recall10.csv", contrast_rows)


# Factorial audit must not copy solution labels into retrieval inputs or use qrels for scores.
status = {
    "experiment": "AX_v23_STAGE1_INPUT_AND_FUSION_CONTROLLED_DIAGNOSTIC",
    "state": "ACTUALLY_EXECUTED",
    "corpus_cases": 84,
    "dev_questions": 10,
    "repeats_per_question": 3,
    "runtime_generated_perspectives": 97,
    "input_conditions": INPUTS,
    "fusion_conditions": FUSIONS,
    "run_conditions": 6,
    "evaluation_k": KS,
    "identical_document_vectors": True,
    "identical_backbone": "BAAI/bge-m3",
    "identical_runtime_perspectives": True,
    "identical_frozen_relevance_labels": True,
    "exact_original_replay_verified": True,
    "same_candidate_pool_all_84_cases": True,
    "no_solution_in_input": True,
    "no_ground_truth_used_in_retrieval_or_fusion": True,
    "llm_called_in_this_diagnostic": False,
    "source_fingerprints_sha256": {str(p.relative_to(ROOT)): sha(p) for p in
        (corpus_file, q_file, gt_file, perspectives_file, embedding_file, old_rank_file, old_branch_file)},
    "status_note": "DEV_ONLY: no frozen data labels modified, not independent Held-out Test",
    "python": platform.python_version(),
    "git_sha": os.getenv("GITHUB_SHA", ""),
}
(OUT / "manifest.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def show_table(ss: list[dict[str, str]]) -> list[str]:
    return [
        "| 검색 입력 | 결과 결합 | Recall@10 | 관점 Coverage@10 | 전략 Coverage@10* |",
        "|---|---|---:|---:|---:|",
        *[
            f"| {x['input_variant']} | {x['fusion']} | {float(x['recall_mean']):.4f} | "
            f"{float(x['perspective_coverage_mean']):.4f} | {float(x['strategy_coverage_mean']):.4f} |"
            for x in ss
        ],
    ]


old_single = [r for r in old_metrics
              if r["system"] == "single_dense_bge_m3" and int(r["k"]) == 10]
old_gpt = [r for r in old_metrics
           if r["system"] == "gpt_only" and int(r["k"]) == 10]
assert len(old_single) == 10 and len(old_gpt) == 30
single_mean = float(np.mean([float(r["recall"]) for r in old_single]))
gpt_mean = float(np.mean([float(r["recall"]) for r in old_gpt]))
at10 = [r for r in summary_rows if r["k"] == 10]
rrtitle = next(x for x in at10 if x["input_variant"] == "TITLE" and x["fusion"] == "ROUND_ROBIN")
assert abs(float(rrtitle["recall_mean"]) - 0.453) < 1e-4

report_lines = [
    "# v2.3 Stage 1 — 검색 입력 × 결과 결합 통제 실험",
    "",
    "실험 조건을 바꾼 **추가 진단(Ablation)**이다. 기존 Stage 1의 84사례, 10질문, 97개 LLM 생성관점, "
    "BAAI/bge-m3, AI 기반 Ground Truth는 그대로 두었다. 새로운 LLM 호출이나 새 데이터 구축 없이 실행하였다.",
    "",
    "## 검증할 질문",
    "1. **검색 입력 검증:** 짧은 관점 제목만 검색해서 관련 정보가 빠진 것은 아닌가?",
    "2. **결과 결합 검증:** 관점별 결과를 돌아가며 1개씩 뽑는 Round-robin이 관련 사례를 밀어낸 것은 아닌가?",
    "",
    "## 실험 설계 (3 × 2)",
    "- 입력 A TITLE: 기존처럼 관점 제목만 사용.",
    "- 입력 B TITLE_DESCRIPTION: 같은 관점 제목 + 설명문 사용.",
    "- 입력 C ORIGINAL_QUERY_WITH_PERSPECTIVE: 원래 업무문제 + 관점 제목 + 설명문 사용.",
    "- 결합 1 ROUND_ROBIN: 기존 방식, 관점마다 돌아가며 사례 선정.",
    "- 결합 2 RRF: 관점별 순위에 대한 Reciprocal Rank Fusion(k=60), 여러 관점에서 중복 발견한 사례를 높게 배치.",
    "- 동일한 BGE-M3로 인코딩한 기존 84사례 벡터를 **그대로 재사용**. 검색 관점은 이전 Stage 1에서 생성한 97개를 그대로 사용.",
    "- **원래 TITLE+ROUND_ROBIN의 97개 개별 branch 순위 및 30개 Top20·모든 지표가 기존 Stage1 기록과 정확히 일치하는지 먼저 검증 PASS**.",
    "- Ground Truth, 전략, 구현/효과, 교수의 참조 관점은 어떤 검색 입력이나 결합 점수에도 넣지 않음.",
    "- 10개 문제마다 3번의 기존 LLM 관점을 사용했으며, 30회 반복을 서로 독립된 30문제로 취급하지 않음.",
    "",
    "## 결과: 같은 조건에서 입력과 결합만 변경한 Recall@10",
    *show_table(at10),
    "",
    "*Strategy Coverage는 **AI 관련도 양성 사례에서 파생한 전략 유형**과의 중복이다. 독립적 전략 추천 정확도가 아니다.",
    "",
    f"**비교용 기존 모델 (재실행 아님, 같은 동결 Stage 1 기록):** "
    f"Single Dense Recall@10 **{single_mean:.4f}**, GPT-only Recall@10 **{gpt_mean:.4f}**.",
    "",
    "## 변화량: 원인 분리를 위한 짝지은 비교",
    "| 바뀐 조건 | Recall@10 평균 변화 | 개선 질문 | 하락 질문 | 동일 질문 | 질문단위 bootstrap 95% 구간 |",
    "|---|---:|---:|---:|---:|---:|",
]
for r in contrast_rows:
    report_lines.append(
        f"| {r['contrast']} | {r['recall10_delta_mean']:+.4f} | "
        f"{r['queries_improved']} | {r['queries_declined']} | {r['queries_tied']} | "
        f"[{r['ci95_query_bootstrap_low']:+.4f}, {r['ci95_query_bootstrap_high']:+.4f}] |"
    )
report_lines += [
    "",
    "Bootstrap 구간은 **개발용 10질문의 차이**를 설명하기 위한 탐색적 구간이다. 새로운 문제에 대한 일반화의 통계적 보증이나 모델 선정의 최종 검증으로 사용하지 않는다.",
    "",
    "## 추가 점검",
    "- Top10 기존 대비 새로 찾은 정답 사례(gained)와 잃은 사례(lost)를 **동시에** 기록하였다.",
    "- 관점별 검색결과의 중복률과 최종 상위 사례가 어느 관점의 후보였는지 기록하였다.",
    "- 신규 검색 문장의 길이와 SHA256을 \`input_text_audit.csv\`에 남겼다.",
    "- Reference Perspective 중 정답 사례가 0개인 하나의 관점은 Coverage 분모에서 제외하였다(억지 정답 생성 금지).",
    "",
    "## 해석 및 연구 설계상 주의",
    "- 이 실험은 **교수 제안 아키텍처의 원리 검증**을 위한 진단이며 RRF로 교수의 branch 보존 구조를 최종 대체한다는 뜻은 아니다.",
    "- RRF가 유리해도 다중 관점의 식별성과 분기별 근거를 별도로 보존·검증해야 한다.",
    "- TITLE+DESCRIPTION과 원문 추가 간 차이는 모델/정답을 바꾸지 않은 상태에서 검색 텍스트의 정보량 효과이다.",
    "- Stage1/2/3/4 완료 기록 및 동결 데이터셋은 변경하지 않음. Dev 실험에서 보이는 최고값을 최종 Test 성능으로 주장하지 않음.",
    "",
    "## 재현 파일",
    "- \`factorial_summary.csv\`: 입력 3 × 결합 2 × K 3.",
    "- \`query_level_means.csv\`: 질문별(3회 평균) 지표.",
    "- \`metrics_by_query_and_run.csv\`: 180개 질문-반복-실험조건 × K 3 평가.",
    "- \`replayed_rankings_top20.csv\`: 실제 검색 사례 순위/관점 출처.",
    "- \`top10_gain_loss_vs_original.csv\`: 사례 수준 gain/loss 진단.",
    "- \`paired_contrasts_recall10.csv\`: 변인 통제와 질문별 효과.",
    "- \`input_text_audit.csv\`: 사용한 검색 텍스트 길이 및 해시.",
    "- \`manifest.json\`: 동결 원본 파일 SHA256 및 재현 조건.",
    "",
]
(OUT / "DEV_DIAGNOSTIC_REPORT.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
print("SUCCESS Stage1 input/fusion factorial:", json.dumps(at10, ensure_ascii=False), flush=True)
print("CONTRASTS:", json.dumps(contrast_rows, ensure_ascii=False), flush=True)
