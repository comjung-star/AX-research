import argparse
import json

import numpy as np

from prototype.core import Engine, ROOT
from scripts.build_ax_expansion_release import export_csv, write_json


def main():
    parser = argparse.ArgumentParser(description="Versioned expansion retrieval; no API calls or inherited relevance metrics")
    parser.add_argument("--top-k", type=int, default=10)
    arguments = parser.parse_args()
    if not 1 <= arguments.top_k <= 84:
        raise ValueError("Use the same output budget in the baseline and expanded corpus")
    output = ROOT / "experiments/v24_expansion"
    output.mkdir(parents=True, exist_ok=True)
    counts = {}
    for profile in ("frozen", "active"):
        engine = Engine(profile=profile)
        rows = []
        annotation = []
        for perspective in engine.perspectives:
            key = f"{perspective['query_id']}|{perspective['run_id']}|{perspective['perspective_id']}"
            if key not in engine.branch_vectors:
                raise ValueError("Missing original runtime perspective embedding")
            scores = (engine.views @ engine.branch_vectors[key]).mean(axis=0)
            order = sorted(range(len(engine.case_ids)), key=lambda offset: (-float(scores[offset]), engine.case_ids[offset]))[:arguments.top_k]
            rows.extend({"query_id": perspective["query_id"], "run_id": perspective["run_id"], "perspective_id": perspective["perspective_id"],
                         "perspective_title": perspective["perspective_title"], "rank": rank, "case_id": engine.case_ids[offset],
                         "score": float(scores[offset]), "corpus_version": engine.corpus_version,
                         "corpus_sha256": engine.corpus_hash, "candidate_count": len(engine.cases)} for rank, offset in enumerate(order, 1))
            if profile == "active":
                annotation.extend({"query_id": perspective["query_id"], "run_id": perspective["run_id"], "perspective_id": perspective["perspective_id"],
                                   "case_id": case_id, "status": "UNJUDGED", "relevance_0_4": "", "annotator_id": ""} for case_id in engine.case_ids)
        export_csv(output / (profile + "_dense_topk.csv"), rows, list(rows[0]))
        counts[profile] = {"cases": len(engine.cases), "branches": len(engine.perspectives), "ranking_rows": len(rows), "corpus_sha256": engine.corpus_hash}
        if annotation:
            export_csv(output / "runtime_relevance_annotation_sheet.csv", annotation, list(annotation[0]))
    write_json(output / "run_manifest.json", {"status": "RANKINGS_ONLY_QRELS_UNJUDGED_NOT_PERFORMANCE_CLAIM", "runs": counts,
               "top_k_per_branch": arguments.top_k, "runtime_perspectives": "REUSED_CACHED_DYNAMIC_LLM_OUTPUTS_NOT_GOLD_PERSPECTIVES",
               "scorer": "BGE_M3_NORMALIZED_PROBLEM_TASK_CONTEXT_MEAN_COSINE", "paid_api_calls": 0,
               "note": "Same cached branch queries and output budget. Different case language/coverage are corpus changes, not evidence of model improvement. No prior qrels transferred."})
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
