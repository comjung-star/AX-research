import json
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlsplit

from scripts.build_ax_expansion_release import read_json, write_json
from scripts.review_all_ax_sources import DESTINATION, PacedPublicFetcher, all_inputs, audit_page, transient_access


def main():
    grouped = defaultdict(list)
    for record in all_inputs():
        if record.get("url"):
            grouped[urlsplit(record["url"]).netloc].append(record)
    ready_hosts = []
    candidates = []
    for host, records in grouped.items():
        if not all((DESTINATION / "page_audits" / (record["candidate_id"] + ".json")).exists() for record in records):
            continue
        ready_hosts.append(host)
        for record in records:
            existing = read_json(DESTINATION / "page_audits" / (record["candidate_id"] + ".json"))
            if transient_access(existing.get("access", {})) and not existing.get("prior_access_attempts"):
                candidates.append(record)
    print(json.dumps({"ready_hosts": ready_hosts, "transient_retries": len(candidates)}), flush=True)
    fetcher = PacedPublicFetcher()
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(audit_page, record, fetcher, True) for record in candidates]
        for future in as_completed(futures):
            results.append(future.result())
            if len(results) % 50 == 0:
                print("Retried", len(results), "of", len(candidates), flush=True)
    summary = {"attempted": len(results), "access_statuses": dict(Counter(record["access"]["status"] for record in results)),
               "paid_api_calls": 0, "reason": "One retry for transient failures on hosts whose initial checks are complete"}
    write_json(DESTINATION / "transient_retry_summary.json", summary)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
