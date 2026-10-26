import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.collect_ax_expansion import OUTPUT, ROOT, PublicFetcher


def review_source(candidate, fetcher, destination):
    target = destination / (candidate["candidate_id"] + ".json")
    if target.exists():
        return json.loads(target.read_text(encoding="utf-8"))
    access, payload = fetcher.get(candidate["url"])
    soup = BeautifulSoup(payload, "html.parser")
    for hidden in soup.select("script,style,nav,header,footer,noscript,form,[role=navigation],[role=banner]"):
        hidden.decompose()
    body = soup.find("main") or soup.find("article") or soup.body or soup
    paragraphs = list(dict.fromkeys(element.get_text(" ", strip=True) for element in body.find_all(["p", "h1", "h2", "h3", "li"])))
    record = {"candidate_id": candidate["candidate_id"], "url": candidate["url"], "access": access,
              "paragraphs": [paragraph for paragraph in paragraphs if len(paragraph) > 45]}
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--urls", nargs="+", required=True)
    arguments = parser.parse_args()
    candidates = json.loads((OUTPUT / "candidates.json").read_text(encoding="utf-8"))["candidates"]
    candidates += json.loads((OUTPUT / "case_portals/candidates.json").read_text(encoding="utf-8"))["candidates"]
    selected = [candidate for candidate in candidates if candidate["url"] in arguments.urls]
    if len(selected) != len(set(arguments.urls)):
        raise ValueError("Every review URL must resolve to exactly one collected candidate")
    destination = ROOT / ".local/ax-expansion-source-review"
    destination.mkdir(parents=True, exist_ok=True)
    fetcher = PublicFetcher()
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(review_source, candidate, fetcher, destination) for candidate in selected]
        for future in as_completed(futures):
            record = future.result()
            print(record["candidate_id"], record["access"]["status"], len(record["paragraphs"]), flush=True)


if __name__ == "__main__":
    main()
