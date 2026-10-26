"""Read-only DEV provenance/structure checks; no TEST content or web claims."""
import hashlib
import itertools
import re
from collections import defaultdict
from urllib.parse import urlparse
from scripts import query_isolated_revalidation as run


def inspect():
    cases = run.api.read_json(run.DATA / "dev_cases.json")["cases"]
    queries = run.api.read_json(run.DATA / "dev_queries.json")["queries"]
    qrels = run.api.read_csv(run.DATA / "dev_qrels_annotation.csv")
    refs = {(r["query_id"], r["perspective_id"]): r["reference_perspective"] for r in qrels}
    splits = {r["case_id"]: r for r in run.api.read_csv(run.DATA / "split_groups.csv")}
    evidence = {}
    with (run.DATA / "evidence_catalog.jsonl").open(encoding="utf-8") as f:
        for line in f:
            row = run.json.loads(line)
            evidence[row["evidence_id"]] = row
    issues, groups, sources, texts, fingerprints = [], defaultdict(list), defaultdict(list), {}, {}
    hashes = {}
    for c in cases:
        cid = c["case_id"]
        groups[c["leakage_group_id"]].append(cid)
        sources[c["source_url"]].append(cid)
        for field in ("problem", "task", "context", "source_url", "leakage_group_id"):
            if not isinstance(c.get(field), str) or not c[field].strip():
                issues.append({"case_id": cid, "kind": "MISSING_FIELD", "field": field})
        if urlparse(c["source_url"]).scheme not in {"http", "https"}:
            issues.append({"case_id": cid, "kind": "INVALID_SOURCE_URL"})
        if c["partition"] != "DEV_ONLY" or splits[cid]["partition"] != "DEV_ONLY":
            issues.append({"case_id": cid, "kind": "NON_DEV_MEMBER"})
        for eid in c["evidence_ids"]:
            e = evidence.get(eid, {})
            if e.get("case_id") != cid or e.get("source_url") != c["source_url"]:
                issues.append({"case_id": cid, "kind": "SOURCE_MAPPING_MISMATCH"})
                continue
            path = e["evidence_locator"].split("#")[0]
            if path not in hashes:
                hashes[path] = hashlib.sha256((run.ROOT / path).read_bytes()).hexdigest()
            if hashes[path] != e["evidence_sha256"]:
                issues.append({"case_id": cid, "kind": "EVIDENCE_FILE_HASH_MISMATCH"})
        text = re.sub(r"\s+", " ", " ".join(c[f] for f in ("problem", "task", "context"))).strip().casefold()
        texts[cid] = text
        fingerprints[cid] = {text[i:i+3] for i in range(len(text)-2)}
    duplicates = []
    for a, b in itertools.combinations(texts, 2):
        fa, fb = fingerprints[a], fingerprints[b]
        similarity = len(fa & fb) / len(fa | fb) if fa | fb else 1
        if similarity >= .45:
            duplicates.append({"case_a": a, "case_b": b, "character_trigram_jaccard": similarity, "exact_ptc": texts[a] == texts[b]})
    result = {"stage": "PRECHECK_NOT_STAGE1_LABELS", "case_count": len(cases), "query_count": len(queries), "reference_count": len(refs),
              "structural_issues": issues, "leakage_group_count": len(groups),
              "shared_leakage_groups": {g: ids for g, ids in groups.items() if len(ids) > 1},
              "shared_source_urls": {s: ids for s, ids in sources.items() if len(ids) > 1},
              "similarity_candidates_not_deletions": duplicates,
              "exact_ptc_duplicate_pairs": sum(r["exact_ptc"] for r in duplicates),
              "source_file_hashes": hashes, "independent_web_fact_verification_performed": False,
              "human_validation_count": 0, "test_content_read": False, "original_data_modified": False,
              "all_queries_are_dev": True, "query_suitability": "TEN_EXISTING_BUSINESS_PROBLEMS; TASK_OVERLAP_ALLOWED; NO_HELDOUT_GENERALIZATION_CLAIM",
              "reference_grounding": "PENDING_SEMANTIC_REVIEW; NOT_APPROVED_FOR_PRIMARY_REFERENCE_COVERAGE",
              "reference_texts": [{"query_id": q, "perspective_id": p, "text": t} for (q,p), t in refs.items()],
              "judges_required": run.CONFIG["independent_judges_required"],
              "zero_relevant_policy": "Keep query; precision denominator K. Recall/F1 undefined where approved relevant total is zero; report zero-relevant query count and macro denominators, never fabricate positives.",
              "unresolved_policy": "Never convert unjudged/disputed to irrelevant; do not release definitive retrieval metrics until label gate is resolved.",
              "retry_policy": "One known-format retry, no automatic uncertain transport replay; durable attempt reservations and known-response resume.",
              "api_rates": run.CONFIG["generation_minimum_interval_seconds"]}
    run.save(run.OUTPUT / "data_precheck.json", result)
    return result


if __name__ == "__main__":
    import json
    r = inspect()
    print(json.dumps({k:r[k] for k in ("case_count", "query_count", "reference_count", "structural_issues", "leakage_group_count", "exact_ptc_duplicate_pairs")},ensure_ascii=False))
