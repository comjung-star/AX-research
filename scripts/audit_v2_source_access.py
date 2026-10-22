"""Inventory source accessibility without treating downloads as source verification."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(re.sub(r"\s+", " ", data.strip()))


def fetch(url):
    record = {"url": url, "accessed_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "", "final_url": "", "http_status": "", "sha256": "",
              "visible_characters": 0, "error": ""}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AXResearchSourceAudit/2"})
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read(8_000_000)
            record.update(final_url=response.url, http_status=response.status,
                          sha256=hashlib.sha256(payload).hexdigest())
            if "text/html" not in response.headers.get("Content-Type", ""):
                record["status"] = "NON_HTML_REQUIRES_MANUAL_REVIEW"
                return record
            parser = VisibleText()
            parser.feed(payload.decode(response.headers.get_content_charset() or "utf-8", errors="replace"))
            visible = "\n".join(parser.parts)
            record.update(status="FETCHED_NOT_SEMANTICALLY_VERIFIED", visible_characters=len(visible))
            cache = ROOT / ".cache/v2-source-access"
            cache.mkdir(parents=True, exist_ok=True)
            (cache / (hashlib.sha256(url.encode()).hexdigest() + ".txt")).write_text(visible, encoding="utf-8")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
        record.update(status="ACCESS_FAILED", error=str(error)[:300])
    return record


def run():
    with (ROOT / "data/v2/main_case_parent_staging_v2.csv").open(encoding="utf-8-sig", newline="") as handle:
        parents = list(csv.DictReader(handle))
    associations = {row["parent_v1_case_id"]: re.findall(r"https?://[^\s;]+", row["original_source"]) for row in parents}
    urls = sorted({url for sources in associations.values() for url in sources})
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = dict(zip(urls, pool.map(fetch, urls)))
    output = [{"parent_case_id": parent, **results[url]} for parent, sources in associations.items() for url in sources]
    path = ROOT / "data/v2/source_access_audit_v2.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    print(json.dumps({"parents": len(parents), "unique_urls": len(urls),
                      "failed_urls": sum(row["status"] == "ACCESS_FAILED" for row in results.values()),
                      "semantic_verification": "NOT_PERFORMED_BY_THIS_SCRIPT"}))


if __name__ == "__main__":
    run()
