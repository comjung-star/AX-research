#!/usr/bin/env python3
"""Frozen v2.3 Stage-1 factor-isolation diagnostic: input text x branch merger.

Primary: Recall@10, 10 distinct DEV questions (3 repeats nested within query).
Controlled: same 84 cases, 97 existing LLM perspectives, same frozen BGE-M3
case embeddings, same independent AI-created DEV relevance matrix.
No solutions/strategies/outcomes/relevance are read by runtime retrieval.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import os
import platform
from collections import defaultdict, OrderedDict
from pathlib import Path

import numpy as np
from ax_research.selection import branch_balanced_unique

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "experiments/v23_dev/stage1"
OUT = ROOT / "experiments/v23_dev/stage1_input_merge_diagnostic"
DATA = ROOT / "data/v2_3"
KS = (5, 10, 20)
INPUTS = ("title_only", "title_description", "query_title_description")
MERGERS = ("round_robin", "rrf60")
MODEL = "BAAI/bge-m3"
SEED = 20261024

def csv_read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def csv_write(path, rows):
    if not rows: raise ValueError("Empty CSV: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def emit_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def mean(values):
    return float(np.mean(np.asarray(values, dtype=np.float64)))

def rrf60(branches, all_ids):
    scores = defaultdict(float)
    for ranking in branches.values():
        for i, cid in enumerate(ranking, start=1):
            scores[cid] += 1.0 / (60 + i)
    if set(scores) != set(all_ids):
        raise ValueError("RRF missing case IDs")
    return sorted(scores, key=lambda cid: (-scores[cid], cid))

def rr(branches, n):
    return [cid for _, cid in branch_balanced_unique(branches, k=n)]

def similarity_scores(vecs, query):
    return vecs @ query

def order(scores, case_ids):
    return [case_ids[i] for i in sorted(range(len(case_ids)), key=lambda i: (-float(scores[i]), case_ids[i]))]

def calculate(ranked, qid, positives, strategies):
    relevant = set().union(*positives[qid].values())
    present = [x for x in positives[qid].values() if x]
    expected_strategies = {strategy for cid in relevant for strategy in strategies[cid]}
    out = []
    for k in KS:
        picked = set(ranked[:k])
        picked_strategies = {strategy for cid in picked for strategy in strategies[cid]}
        out.append({
            "k": k,
            "recall": len(picked & relevant) / len(relevant) if relevant else None,
            "perspective_coverage": sum(bool(picked & p) for p in present) / len(present) if present else None,
            "strategy_coverage_derived": len(picked_strategies & expected_strategies) / len(expected_strategies) if expected_strategies else None,
            "relevant_total": len(relevant),
            "answerable_perspectives": len(present),
            "empty_perspectives_excluded": len(positives[qid]) - len(present),
        })
    return out

def branch_overlap(ranks):
    top = [set(x[:10]) for x in ranks.values()]
    pairwise = [len(a & b) / len(a | b) for a, b in itertools.combinations(top, 2)]
    return float(mean(pairwise)) if pairwise else 0.0

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    npz = np.load(SRC / "fixed_bge_m3_embeddings.npz", allow_pickle=False)
    cids = npz["case_ids"].tolist()
    assert len(cids) == len(set(cids)) == 84
    cid_to_index = {cid: i for i, cid in enumerate(cids)}
    doc_embeddings = npz["document_embeddings"].astype(np.float32)
    assert doc_embeddings.shape[0] == len(cids)
    query_candidates = json.loads((DATA/"dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))["queries"]
    query_texts = {q["query_id"]: q["business_problem_query"] for q in query_candidates}
    assert len(query_texts) == 10
    frozen_cases = json.loads((DATA/"main_cases_v2_3.json").read_text(encoding="utf-8"))["cases"]
    assert {c["case_id"] for c in frozen_cases} == set(cids)
    strategies = {c["case_id"]: c["strategy_labels"] for c in frozen_cases}
    defs = json.loads((SRC / "generated_runtime_perspectives.json").read_text(encoding="utf-8"))
    old_keys = npz["branch_keys"].tolist()
    keys = [f"{b['query_id']}|{int(b['run_id'])}|{b['perspective_id']}" for b in defs]
    assert old_keys == keys and len(keys) == len(set(keys)) == 97
    pos = defaultdict(lambda: defaultdict(set))
    all_rows = csv_read(DATA/"ground_truth/silver_dev_qrels_2520.csv")
    assert len(all_rows) == 2520
    for r in all_rows:
        if r["provenance"] != "AI_THREE_PASS_MEDIAN_NOT_HUMAN_GOLD":
            raise ValueError("Ground Truth provenance changed unexpectedly")
        q, p, case = r["query_id"],r["perspective_id"],r["case_id"]
        pos[q][p] |= ({case} if int(r["relevance_0_4"]) >= 3 else set())
    assert set(pos) == set(query_texts)
    assert all(len(pos[q]) == 3 for q in pos)
    old_rankings = csv_read(SRC/"rankings_top20.csv")
    old_map = defaultdict(list)
    for r in old_rankings:
        if r["system"]=="mp_dense_bge_m3":
            old_map[(r["query_id"], int(r["run_id"]))].append(r)
    assert len(old_map)==30
    for rows in old_map.values(): rows.sort(key=lambda x:int(x["rank"]))
    saved_branch = csv_read(SRC/"branch_rankings.csv")
    saved_dense = defaultdict(list)
    for r in saved_branch:
        if r["retrieval"] == "dense":
            saved_dense[(r["query_id"],int(r["run_id"]),r["perspective_id"])].append(r)
    assert len(saved_dense)==97
    for rows in saved_dense.values():
        rows.sort(key=lambda x:int(x["local_rank"]))
        assert len(rows) == 84

    # Only generated perspective content; reference perspectives and qrels are NOT part of embeddings.
    text_variants = {
        "title_only": [b["perspective_title"] for b in defs],
        "title_description": [
            f"{b['perspective_title']}\n{b['perspective_description']}" for b in defs
        ],
        "query_title_description": [
            f"업무 문제: {query_texts[b['query_id']]}\n"
            f"문제 관점: {b['perspective_title']}\n"
            f"관점 설명: {b['perspective_description']}" for b in defs
        ],
    }
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL, device="cpu")
    # Cross-run comparability: verify current encoder matches the saved Stage 1 vectors.
    fresh_titles = model.encode(text_variants["title_only"], normalize_embeddings=True,
                                convert_to_numpy=True, show_progress_bar=False).astype(np.float32)
    old_titles = npz["branch_embeddings"].astype(np.float32)
    assert fresh_titles.shape == old_titles.shape
    per_title_cos = np.einsum("ij,ij->i", fresh_titles, old_titles)
    min_title_cos = float(per_title_cos.min())
    if min_title_cos < 0.999:
        raise RuntimeError(f"Model revision drift: min cosine old/fresh title embeddings {min_title_cos:.6f}")
    vectors = {"title_only": old_titles}
    for setting in ("title_description", "query_title_description"):
        vectors[setting] = model.encode(text_variants[setting],
                           normalize_embeddings=True, convert_to_numpy=True,
                           show_progress_bar=False).astype(np.float32)
    branches = defaultdict(lambda: OrderedDict())
    branch_rows = []
    for setting in INPUTS:
        for b, qemb in zip(defs, vectors[setting]):
            q, run, pid = b["query_id"], int(b["run_id"]), b["perspective_id"]
            ranked = order(similarity_scores(doc_embeddings, qemb), cids)
            branches[(setting,q,run)][pid] = ranked
            if setting=="title_only":
                historical = [r["case_id"] for r in saved_dense[(q,run,pid)]]
                if ranked != historical:
                    raise AssertionError(f"Frozen original branch ranking not reproduced: {q}/{run}/{pid}")
            for index, cid in enumerate(ranked,1):
                branch_rows.append({
                    "input":setting, "query_id":q, "run_id":run,
                    "perspective_id":pid, "rank":index, "case_id":cid,
                    "cosine_score":float(doc_embeddings[cid_to_index[cid]]@qemb),
                })
    assert len(branches)==3*30
    metrics_rows, result_rows, diagnostic_rows = [], [], []
    for setting in INPUTS:
        for q in query_texts:
            for run in (1,2,3):
                br = branches[(setting,q,run)]
                if not 2<=len(br)<=5: raise AssertionError(f"Bad branch count: {q}/{run}")
                diagnostics = dict(input=setting,query_id=q,run_id=run,
                    runtime_branch_count=len(br),branch_top10_jaccard=branch_overlap(br),
                    mean_branch_query_chars=mean([len(text_variants[setting][keys.index(f"{q}|{run}|{pid}")]) for pid in br]))
                diagnostic_rows.append(diagnostics)
                choices = {
                    "round_robin":rr(br,84),
                    "rrf60":rrf60(br,cids),
                }
                for merging, ranked in choices.items():
                    assert len(ranked)==84 and len(set(ranked))==84
                    if setting=="title_only" and merging=="round_robin":
                        historical = [r["case_id"] for r in old_map[(q,run)]]
                        assert ranked[:20] == historical, f"Cannot reproduce frozen Stage1: {q}/{run}"
                    for m in calculate(ranked,q,pos,strategies):
                        metrics_rows.append({"input":setting,"merge":merging,"query_id":q,"run_id":run,**m})
                    for i,cid in enumerate(ranked[:20],start=1):
                        result_rows.append({"input":setting,"merge":merging,
                                            "query_id":q,"run_id":run,
                                            "rank":i,"case_id":cid})
    csv_write(OUT/"metrics_all_540.csv",metrics_rows)
    csv_write(OUT/"rankings_top20_all_combinations.csv",result_rows)
    csv_write(OUT/"branch_rankings_all_84.csv",branch_rows)
    csv_write(OUT/"branch_overlap_diagnostics.csv",diagnostic_rows)

    # Query-level aggregation: average repeated LLM generated perspectives within each question.
    query_rows=[]
    for setting in INPUTS:
        for merging in MERGERS:
            for q in query_texts:
                for k in KS:
                    select=[x for x in metrics_rows if x["input"]==setting and x["merge"]==merging and x["query_id"]==q and x["k"]==k]
                    assert len(select)==3
                    query_rows.append({"input":setting,"merge":merging,"query_id":q,"k":k,
                       "recall":mean([x["recall"] for x in select]),
                       "perspective_coverage":mean([x["perspective_coverage"] for x in select]),
                       "strategy_coverage_derived":mean([x["strategy_coverage_derived"] for x in select])})
    csv_write(OUT/"query_level_metrics.csv",query_rows)
    summary=[]
    for setting in INPUTS:
        for merging in MERGERS:
            for k in KS:
                these=[x for x in query_rows if x["input"]==setting and x["merge"]==merging and x["k"]==k]
                assert len(these)==10
                summary.append({"input":setting,"merge":merging,"k":k,
                    "independent_queries":10,"repeats_per_query":3,
                    "recall_mean":mean([x["recall"] for x in these]),
                    "perspective_coverage_mean":mean([x["perspective_coverage"] for x in these]),
                    "strategy_coverage_derived_mean":mean([x["strategy_coverage_derived"] for x in these])})
    csv_write(OUT/"summary_18_combinations.csv",summary)

    baseline={r["query_id"]:r["recall"] for r in query_rows if r["input"]=="title_only" and r["merge"]=="round_robin" and r["k"]==10}
    comparisons=[]
    for setting in INPUTS:
        for merging in MERGERS:
            arr=[r for r in query_rows if r["input"]==setting and r["merge"]==merging and r["k"]==10]
            delta = np.asarray([r["recall"] - baseline[r["query_id"]] for r in arr],dtype=float)
            gen = np.random.default_rng(SEED)
            resample = gen.integers(0,10,size=(10000,10))
            bmeans=np.mean(delta[resample],axis=1)
            comparisons.append(dict(input=setting,merge=merging,mean_delta_recall_at10=mean(delta),
              improved_questions=int(np.sum(delta>1e-8)),worsened_questions=int(np.sum(delta<-1e-8)),
              tied_questions=int(np.sum(np.abs(delta)<=1e-8)),
              paired_question_bootstrap_ci95_low=float(np.quantile(bmeans,.025)),
              paired_question_bootstrap_ci95_high=float(np.quantile(bmeans,.975))))
    csv_write(OUT/"paired_query_deltas_vs_original.csv",comparisons)

    # Strict historical validation: original title+round-robin scores exactly reproduced.
    control = [r for r in summary if r["input"]=="title_only" and r["merge"]=="round_robin" and r["k"]==10][0]
    if abs(control["recall_mean"]-0.453) > 0.0001:
        raise AssertionError("Stage 1 control score drifted")
    manifest=dict(status="REAL_STAGE1_DIAGNOSTIC_SUCCESS",
       protocol="PREDEFINED_INPUT_AND_MERGE_FACTORIAL_3x2",
       corpus="v2.3 frozen 84",dev_query_count=10,reference="LLM 3-pass median 2520",
       stage1_original_same_case_vectors=True,
       stage1_original_perspectives_replayed_exactly=True,
       original_title_branch_rankings_exact=True,
       original_title_round_robin_top20_rankings_exact=True,
       model_revision_match_min_cos=min_title_cos,
       input_modes=INPUTS,merge_modes=MERGERS,ks=KS,
       repeats_per_query=3,branches=len(defs),
       primary="Recall@10",secondary=["Perspective Coverage@10","Derived Strategy Coverage@10"],
       CI="paired bootstrap over 10 distinct Dev queries, seed 20261024; exploratory only",
       no_gt_exposure_at_runtime=True,no_test_data=True,
       qa="no optimization or tuning based on observed values",
       python=platform.python_version(),sentence_transformers="runtime BAAI/bge-m3")
    emit_json(OUT/"manifest.json",manifest)
    result_str = "\n".join(
       f"| {s['input']} | {s['merge']} | {s['recall_mean']:.4f} | {s['perspective_coverage_mean']:.4f} | {s['strategy_coverage_derived_mean']:.4f} |"
       for s in summary if s["k"]==10)
    delta_str = "\n".join(
       f"| {x['input']} | {x['merge']} | {x['mean_delta_recall_at10']:+.4f} | "
       f"{x['improved_questions']} / {x['worsened_questions']} / {x['tied_questions']} | "
       f"[{x['paired_question_bootstrap_ci95_low']:+.4f}, {x['paired_question_bootstrap_ci95_high']:+.4f}] |"
       for x in comparisons)
    best=max((r for r in summary if r["k"]==10),key=lambda r:r["recall_mean"])
    report = f"""# Stage 1 — 검색 입력·결과 결합 원인 진단 (v2.3)

**상태:** 실제 재실험 완료. 기존 Stage1 모든 관점과 기준 결과를 정확히 재현한 뒤 변경 요인을 분리해서 비교.

## 무엇을 고정했나
- 업무 AX 사례 84개·Dev 질의 10개·AI 관련도 평가 2,520개(3회 중앙값), 기존 BGE-M3 사례 임베딩.
- 이전에 AI가 생성한 **97개 관점**과 질의당 3회 평가를 그대로 재사용. 추가 LLM 관점 재생성 없음.
- 이전 Stage1 title-only + round-robin의 **분기 전체 84개 순위와 최종 Top20을 전부 일치 검증**.
- 주지표 Recall@10; K=5/10/20도 원자료 제공. 질문당 3회 평균 후 10개 질문 평균.
- AI 정답·전략·사례 구현 성과는 검색 입력으로 전달하지 않음.

## 바꾼 요인
- **검색 입력:** title_only = 관점 제목 / title_description = 제목+설명 / query_title_description = 원문 업무문제+제목+설명.
- **결과 결합:** round_robin = 관점마다 1개씩 고유 사례 추출 / rrf60 = 관점별 rank의 역수 합(\`sum(1/(60+rank))\`)으로 공통 사례 순위.
- 모든 분기는 84개 전체 사례에 대해 순위를 매기므로, 모든 방식이 같은 코퍼스·검색 후보 접근권을 가짐.

## 6가지 실험 결과 — K=10
| 검색 입력 | 결과 결합 | Recall@10 | 관점 Coverage@10 | 전략 Coverage@10* |
|---|---|---:|---:|---:|
{result_str}

* 전략 Coverage는 관련으로 판정된 사례의 사전 Strategy 라벨 합집합을 사용한 파생 보조지표. 독립 전략 Gold 아님.

## 최초 Stage 1(title-only + round-robin) 대비 질문 단위 변화
| 입력 | 결합 | Recall@10 변화 | 개선/하락/동률 질문 | 10개 질문 재표본 bootstrap 95% 구간 |
|---|---|---:|---:|---|
{delta_str}

## 최고값(Dev 탐색)
- 이번 6개 조합 중 최고 **{best['input']} + {best['merge']}**: Recall@10 **{best['recall_mean']:.4f}**.
- 이는 **새로운 검증 데이터에 대한 일반화 성능이 아님**. 개발 질문으로 비교한 결과이며 최종 모델 변경 여부는 별도로 사전 정의된 기준을 따를 것.

## 해석 주의
- 비교 대상은 교수님 제안 **Stage1 다중관점 Dense 검색 구현의 입력과 결합**이다. 교수님 아키텍처 전체(학습형 Gated Fusion/MLP/Evidence)를 검증하는 실험은 아니다.
- 관점 제목에 설명이나 원본 질의를 추가했을 때 성능 변화는 원인 진단용 비교이며, 유리한 조합을 사후 최종 성능으로 광고하지 않는다.
- bootstrap 구간은 질문 10개만을 다시 뽑은 탐색적 불확실성이다. 3회 재실험은 서로 독립적인 30개 질문이 아니다.
- 기존 v2.3 데이터셋/정답표/Stage1~4 기록은 수정하지 않았다.
"""
    (OUT/"DEV_DIAGNOSTIC_RESULT.md").write_text(report,encoding="utf-8")
    print("STAGE1 INPUT/MERGE SUCCESS", json.dumps(summary,ensure_ascii=False),flush=True)
    print("BEST",json.dumps(best,ensure_ascii=False),flush=True)
    print("DELTA",json.dumps(comparisons,ensure_ascii=False),flush=True)

if __name__ == "__main__":
    main()
