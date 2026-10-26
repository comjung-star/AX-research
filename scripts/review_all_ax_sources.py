import argparse
import hashlib
import json
import re
import threading
import time
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
import requests

from scripts.build_ax_expansion_release import read_json, source_records, write_json
from scripts.collect_ax_expansion import OUTPUT, ROOT, PublicFetcher, USER_AGENT, limited_text, timestamp
from scripts.collect_ax_portals import SOURCES, normalize_eu, normalize_us, parse_csv


DESTINATION = ROOT / "collections/ax-review-all-2026-10-26"
PRIVATE_TEXT = ROOT / ".local/ax-all-source-text"


def transient_access(access):
    return access.get("status") in {"ACCESS_FAILED", "PARSER_OR_ACCESS_ERROR"} or (access.get("http_status") or 0) >= 500 or (access.get("status") == "ROBOTS_DENIED_OR_UNAVAILABLE" and (access.get("robots_status") is None or access.get("robots_status", 0) >= 500))


class PacedPublicFetcher(PublicFetcher):
    def __init__(self):
        super().__init__()
        self.start_locks = defaultdict(threading.Lock)
        self.slots = defaultdict(lambda: threading.Semaphore(8))
        self.next_start = defaultdict(float)
        self.sessions = threading.local()

    def get(self, url):
        host = urlsplit(url).netloc
        parser, available, robots_status = self.policy(host)
        result = {"url": url, "accessed_at": timestamp(), "robots_status": robots_status, "status": "", "http_status": None}
        if not available or not parser.can_fetch(USER_AGENT, url):
            result["status"] = "ROBOTS_DENIED_OR_UNAVAILABLE"
            return result, b""
        with self.slots[host]:
            with self.start_locks[host]:
                time.sleep(max(0, self.next_start[host] - time.monotonic()))
                self.next_start[host] = time.monotonic() + max(0.6, parser.crawl_delay(USER_AGENT) or 0)
            if not hasattr(self.sessions, "client"):
                self.sessions.client = requests.Session()
            try:
                with self.sessions.client.get(url, timeout=(8, 25), headers={"User-Agent": USER_AGENT}, stream=True) as response:
                    payload = bytearray()
                    truncated = False
                    for chunk in response.iter_content(65536):
                        payload.extend(chunk)
                        if response.status_code != 200:
                            break
                        if len(payload) > 8_000_000:
                            truncated = True
                            break
                    if response.status_code == 429:
                        try:
                            backoff = max(60, int(response.headers.get("Retry-After", "60")))
                        except ValueError:
                            backoff = 60
                        with self.start_locks[host]:
                            self.next_start[host] = max(self.next_start[host], time.monotonic() + backoff)
                    result.update(http_status=response.status_code, final_url=response.url, content_type=response.headers.get("Content-Type", ""),
                        payload_sha256=hashlib.sha256(payload).hexdigest(), bytes_read=len(payload), truncated=truncated,
                        error_response_prefix_only=response.status_code != 200,
                        status="FETCHED" if response.status_code == 200 and not truncated else "HTTP_ERROR_OR_TRUNCATED")
                    return result, bytes(payload)
            except requests.RequestException as error:
                result.update(status="ACCESS_FAILED", error_type=type(error).__name__)
                return result, b""


def all_inputs():
    records = source_records()
    for source in SOURCES:
        payload = (OUTPUT / "portals/source_datasets" / (source["id"] + ".csv")).read_bytes()
        _, valid, malformed = parse_csv(payload)
        if malformed:
            raise ValueError("Corrected CSV parser still found misaligned original rows")
        normalize = normalize_us if source["id"] == "US_OMB_2025" else normalize_eu
        corrected = [normalize(source, offset, values) for offset, values in valid]
        by_row = {record["source_row"]: record for record in corrected}
        by_id = {record["source_record_id"]: record for record in corrected} if source["id"].startswith("EU") else {}
        represented = set()
        for record in records:
            if record.get("source_dataset_id") != source["id"] or record["collection_kind"] != "PUBLIC_SECTOR_INVENTORY":
                continue
            replacement = by_id[record["source_record_id"]] if by_id else by_row[record["source_row"]]
            original_id, original_row = record["candidate_id"], record["source_row"]
            represented.add(replacement["source_row"])
            record.update(replacement)
            record.update(candidate_id=original_id, source_row_before_csv_fix=original_row,
                          csv_parse_method="STANDARD_DOUBLE_QUOTE_ESCAPING", collection_kind="PUBLIC_SECTOR_INVENTORY")
        for record in corrected:
            if record["source_row"] not in represented:
                stable_id = re.sub(r"[^A-Za-z0-9_]", "_", record["source_record_id"])
                records.append({**record, "candidate_id": source["id"] + "_RECOVERED_" + stable_id,
                                "collection_kind": "PUBLIC_SECTOR_INVENTORY", "recovered_from_prior_parser": True,
                                "csv_parse_method": "STANDARD_DOUBLE_QUOTE_ESCAPING"})
    processed_keys = {row.get("key") for row in records if row.get("key")}
    for source in read_json(OUTPUT / "discovered_sources.json"):
        if source["key"] not in processed_keys:
            records.append({**source, "candidate_id": "AXC_" + hashlib.sha256(source["key"].encode()).hexdigest()[:14],
                            "collection_kind": "DISCOVERED_SOURCE", "collection_status": "DISCOVERED_NOT_FETCHED"})
    for row in read_json(OUTPUT / "portals/malformed_rows_quarantine.json"):
        records.append({"candidate_id": f"{row['source_dataset_id']}_MALFORMED_{row['source_row']}", "collection_kind": "MALFORMED_SOURCE_ROW",
                        "source_dataset_id": row["source_dataset_id"], "source_row": row["source_row"],
                        "source_record_id": row["values"][0] if row["values"] else "UNKNOWN", "title": row["values"][1] if len(row["values"]) > 1 else "UNKNOWN",
                        "raw_field_count": row["actual_fields"], "expected_field_count": row["expected_fields"],
                        "raw_values_sha256": hashlib.sha256(json.dumps(row["values"], ensure_ascii=False).encode()).hexdigest(),
                        "prior_parser_issue_resolved": True,
                        "recovered_source_record_ids": sorted(set(re.findall(r"\bPSTW-\d+\b", "\n".join(row["values"])))),
                        "source_url": "https://interoperable-europe.ec.europa.eu/collection/public-sector-tech-watch/pstw-cases-viewer-data-download"})
    if len({record["candidate_id"] for record in records}) != len(records):
        raise ValueError("Every collected input must have a unique stable identity")
    return records


def audit_page(source, fetcher, retry_transient=False):
    target = DESTINATION / "page_audits" / (source["candidate_id"] + ".json")
    prior_attempts = []
    if target.exists():
        existing = read_json(target)
        access = existing.get("access", {})
        transient = transient_access(access)
        if not retry_transient or not transient:
            return existing
        prior_attempts = existing.get("prior_access_attempts", []) + [access]
    previous = ROOT / ".local/ax-expansion-source-review" / (source["candidate_id"] + ".json")
    if previous.exists():
        saved = read_json(previous)
        access, paragraphs = saved["access"], saved["paragraphs"]
        title = source.get("source_title") or source.get("source_title_hint") or ""
    else:
        access, payload = fetcher.get(source["url"])
        title = source.get("source_title", "")
        paragraphs = []
        if access["status"] == "FETCHED":
            soup = BeautifulSoup(payload, "html.parser")
            heading = soup.find("h1") or soup.find("title")
            title = heading.get_text(" ", strip=True) if heading else title
            for hidden in soup.select("script,style,nav,header,footer,noscript,form,[role=navigation],[role=banner]"):
                hidden.decompose()
            body = soup.find("main") or soup.find("article") or soup.body or soup
            paragraphs = list(dict.fromkeys(element.get_text(" ", strip=True) for element in body.find_all(["p", "h1", "h2", "h3", "li"])))
            paragraphs = [paragraph for paragraph in paragraphs if len(paragraph) >= 30]
    text = "\n".join(paragraphs)
    result = {"candidate_id": source["candidate_id"], "url": source["url"], "access": access,
              "prior_access_attempts": prior_attempts,
              "source_title": limited_text(title, 20), "paragraph_count": len(paragraphs), "visible_characters": len(text),
              "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "check_status": "PUBLIC_PAGE_FETCH_AND_TEXT_CHECK_COMPLETED",
              "review_method": "AUTOMATED_CONTENT_CHECK_NOT_INDEPENDENT_FACT_VERIFICATION",
              "source_quote_word_count": len(limited_text(title, 20).split()),
              "contains_ai_signal": bool(re.search(r"\b(?:AI|ML|LLM|Claude|GPT|Gemini|Watson|OCR)\b|machine learning|artificial intelligence|인공지능|생성형|머신러닝", text, re.I)),
              "contains_pilot_or_plan_signal": bool(re.search(r"\b(?:pilot|prototype|plan(?:ned|s)?|proof.of.concept)\b|파일럿|시범|계획|실증", text, re.I)),
              "contains_operational_signal": bool(re.search(r"\b(?:deployed|in production|operational|currently uses)\b|운영 중|운영하고|상용화|도입하여", text, re.I))}
    if access["status"] != "FETCHED":
        result["check_status"] = "ACCESS_ATTEMPT_COMPLETED_CONTENT_UNAVAILABLE"
    elif len(text) < 200:
        result["check_status"] = "PAGE_READABLE_CONTENT_INSUFFICIENT"
    private_target = PRIVATE_TEXT / (source["candidate_id"] + ".json")
    write_json(private_target, {"candidate_id": source["candidate_id"], "paragraphs": paragraphs, "text_sha256": result["text_sha256"]})
    temporary = target.with_suffix(".tmp")
    write_json(temporary, result)
    temporary.replace(target)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--retry-transient", action="store_true")
    arguments = parser.parse_args()
    (DESTINATION / "page_audits").mkdir(parents=True, exist_ok=True)
    PRIVATE_TEXT.mkdir(parents=True, exist_ok=True)
    records = all_inputs()
    write_json(DESTINATION / "all_inputs.json", records)
    hosts = defaultdict(deque)
    for record in records:
        if record.get("url"):
            hosts[urlsplit(record["url"]).netloc].append(record)
    pages = []
    while any(hosts.values()):
        for queue in hosts.values():
            if queue:
                pages.append(queue.popleft())
    fetcher = PacedPublicFetcher()
    completed = []
    with ThreadPoolExecutor(max_workers=arguments.workers) as executor:
        futures = {executor.submit(audit_page, source, fetcher, arguments.retry_transient): source for source in pages}
        for future in as_completed(futures):
            source = futures[future]
            try:
                result = future.result()
            except Exception as error:
                result = {"candidate_id": source["candidate_id"], "url": source["url"], "check_status": "CHECK_FAILED",
                          "error_type": type(error).__name__, "access": {"status": "PARSER_OR_ACCESS_ERROR"}, "source_title": source.get("source_title", "")}
                write_json(DESTINATION / "page_audits" / (source["candidate_id"] + ".json"), result)
            completed.append(result)
            if len(completed) % 50 == 0 or len(completed) == len(pages):
                summary = {"all_input_records": len(records), "expected_page_checks": len(pages), "completed_page_checks": len(completed),
                           "page_check_statuses": dict(Counter(row["check_status"] for row in completed)),
                           "access_statuses": dict(Counter(row["access"]["status"] for row in completed)), "paid_api_calls": 0}
                write_json(DESTINATION / "progress.json", summary)
                print(json.dumps(summary, ensure_ascii=False), flush=True)
    write_json(DESTINATION / "page_check_summary.json", summary)


if __name__ == "__main__":
    main()
