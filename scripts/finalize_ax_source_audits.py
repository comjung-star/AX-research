import argparse
import json
import re
from collections import Counter

from scripts.build_ax_expansion_release import read_json, write_json
from scripts.collect_ax_expansion import limited_text
from scripts.review_all_ax_sources import DESTINATION, PRIVATE_TEXT, all_inputs


def finalize(allow_incomplete=False):
    inputs = all_inputs()
    sources = {record["candidate_id"]: record for record in inputs if record.get("url")}
    paths = {path.stem: path for path in (DESTINATION / "page_audits").glob("*.json")}
    missing = set(sources) - set(paths)
    if missing and not allow_incomplete:
        raise ValueError(f"Source checks incomplete: {len(missing)} remaining")
    audits = []
    enriched = 0
    for identifier, path in paths.items():
        audit = read_json(path)
        private = PRIVATE_TEXT / (identifier + ".json")
        if "source_description_excerpt" not in audit and audit.get("access", {}).get("status") == "FETCHED" and private.exists():
            text = read_json(private)
            candidates = [paragraph for paragraph in text["paragraphs"] if paragraph != audit.get("source_title") and not re.search(
                r"cookie|all rights reserved|privacy policy|subscribe|related stories|more stories|copyright|쿠키|개인정보 처리|다른 사례", paragraph, re.I)]
            budget = max(0, 25 - len(audit.get("source_title", "").split()))
            audit["source_description_excerpt"] = limited_text(candidates[0], budget) if candidates else ""
            audit["source_quote_word_count"] = len(audit.get("source_title", "").split()) + len(audit["source_description_excerpt"].split())
            audit["excerpt_basis"] = "VISIBLE_PARAGRAPH_EXCERPT_NOT_A_SEMANTIC_CASE_SUMMARY"
            temporary = path.with_suffix(".finalizing")
            write_json(temporary, audit)
            temporary.replace(path)
            enriched += 1
        audits.append(audit)
    if not missing:
        write_json(DESTINATION / "all_inputs.json", inputs)
        summary = {"all_input_records": len(inputs), "expected_page_checks": len(sources), "completed_page_checks": len(audits),
                   "missing_page_checks": 0, "page_check_statuses": dict(Counter(row["check_status"] for row in audits)),
                   "access_statuses": dict(Counter(row["access"]["status"] for row in audits)),
                   "paid_api_calls": 0, "counts_recomputed_from_saved_records_after_retries": True}
        write_json(DESTINATION / "page_check_summary.json", summary)
        write_json(DESTINATION / "progress.json", summary)
    result = {"checked_records_present": len(audits), "missing": len(missing), "new_excerpts": enriched}
    print(json.dumps(result), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-incomplete", action="store_true")
    arguments = parser.parse_args()
    finalize(arguments.allow_incomplete)


if __name__ == "__main__":
    main()
