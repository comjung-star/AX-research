import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
PROMPT = "Reply with exactly OK."
OUTPUT_LIMIT = 64
TEST_BUDGET_USD = 0.01
PROVIDERS = {
    "openai": {"env": "OPENAI_API_KEY", "model": "gpt-6-luna", "input_price": 0.10, "output_price": 0.50,
               "url": "https://api.openai.com/v1/responses"},
    "gemini": {"env": "GEMINI_API_KEY", "model": "gemini-2.5-flash-lite", "input_price": 0.10, "output_price": 0.40,
               "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"},
    "claude": {"env": "ANTHROPIC_API_KEY", "model": "claude-haiku-4-5-20251001", "input_price": 1.00, "output_price": 5.00,
               "url": "https://api.anthropic.com/v1/messages"},
}


def read_key(name):
    value = os.environ.get(name)
    if value:
        return value.strip()
    if os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
                return str(winreg.QueryValueEx(handle, name)[0]).strip()
        except FileNotFoundError:
            pass
    return None


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        raise urllib.error.HTTPError(request.full_url, code, "Redirect blocked", headers, response)


def request_spec(provider, key):
    spec = PROVIDERS[provider]
    headers = {"Content-Type": "application/json"}
    if provider == "openai":
        headers["Authorization"] = "Bearer " + key
        body = {"model": spec["model"], "input": PROMPT, "max_output_tokens": OUTPUT_LIMIT,
                "reasoning": {"effort": "none"}, "store": False}
    elif provider == "gemini":
        headers["x-goog-api-key"] = key
        body = {"contents": [{"parts": [{"text": PROMPT}]}],
                "generationConfig": {"maxOutputTokens": OUTPUT_LIMIT, "thinkingConfig": {"thinkingBudget": 0}}}
    else:
        headers["x-api-key"] = key
        headers["anthropic-version"] = "2023-06-01"
        body = {"model": spec["model"], "max_tokens": OUTPUT_LIMIT,
                "messages": [{"role": "user", "content": PROMPT}]}
    return spec["url"], headers, body


def error_category(status, body):
    lower = body.lower()
    if "credit balance" in lower or "insufficient_quota" in lower or "billing" in lower:
        return "BILLING_OR_CREDIT_BLOCKED"
    if status in (401, 403):
        return "AUTHENTICATION_OR_PERMISSION_FAILED"
    if status == 404:
        return "MODEL_OR_ENDPOINT_UNAVAILABLE"
    if status == 429:
        return "RATE_OR_QUOTA_LIMITED"
    if status in (400, 422):
        return "INVALID_REQUEST"
    if 300 <= status < 400:
        return "REDIRECT_BLOCKED"
    return "HTTP_ERROR"


def nonnegative_integer(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def summarize_response(provider, payload):
    if provider == "openai":
        usage = payload.get("usage", {})
        input_tokens = nonnegative_integer(usage.get("input_tokens"))
        output_tokens = nonnegative_integer(usage.get("output_tokens"))
        text = "".join(part.get("text", "") for item in payload.get("output", []) for part in item.get("content", []) if part.get("type") == "output_text")
    elif provider == "gemini":
        usage = payload.get("usageMetadata", {})
        input_tokens = nonnegative_integer(usage.get("promptTokenCount"))
        candidates = nonnegative_integer(usage.get("candidatesTokenCount"))
        thoughts = nonnegative_integer(usage.get("thoughtsTokenCount", 0))
        output_tokens = candidates + thoughts if candidates is not None and thoughts is not None else None
        text = "".join(part.get("text", "") for candidate in payload.get("candidates", []) for part in candidate.get("content", {}).get("parts", []) if not part.get("thought", False))
    else:
        usage = payload.get("usage", {})
        input_tokens = nonnegative_integer(usage.get("input_tokens"))
        output_tokens = nonnegative_integer(usage.get("output_tokens"))
        text = "".join(part.get("text", "") for part in payload.get("content", []) if part.get("type") == "text")
    model = payload.get("model", payload.get("modelVersion", PROVIDERS[provider]["model"]))
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9._:/-]{1,100}", model) or not model.startswith(("gpt-", "gemini-", "claude-")):
        model = "RESPONSE_MODEL_NOT_RECORDED"
    price = PROVIDERS[provider]
    cost = (input_tokens * price["input_price"] + output_tokens * price["output_price"]) / 1_000_000 if input_tokens is not None and output_tokens is not None else None
    return {"status": "SUCCESS" if text.strip() else "HTTP_OK_WITHOUT_VISIBLE_TEXT", "response_model": model,
            "response_nonempty": bool(text.strip()), "response_matches_OK": text.strip() == "OK",
            "input_tokens": input_tokens, "output_tokens_including_reported_thinking": output_tokens,
            "estimated_standard_token_cost_usd": cost}


def send_once(provider, key):
    url, headers, body = request_spec(provider, key)
    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    start = time.monotonic()
    try:
        opener = urllib.request.build_opener(RejectRedirects())
        with opener.open(request, timeout=45) as response:
            payload = json.loads(response.read(1_000_000))
            result = {"http_status": response.status, **summarize_response(provider, payload)}
    except urllib.error.HTTPError as error:
        body_text = error.read(65536).decode("utf-8", errors="replace")
        result = {"http_status": error.code, "status": error_category(error.code, body_text), "estimated_standard_token_cost_usd": None}
    except (urllib.error.URLError, TimeoutError, OSError):
        result = {"http_status": None, "status": "TRANSPORT_ERROR_NO_RETRY_POSSIBLY_BILLED", "estimated_standard_token_cost_usd": None}
    except (ValueError, TypeError, KeyError, AttributeError):
        result = {"http_status": None, "status": "UNPARSEABLE_RESPONSE_NO_RETRY", "estimated_standard_token_cost_usd": None}
    return {"provider": provider, "requested_model": PROVIDERS[provider]["model"], "attempts": 1,
            "elapsed_seconds": round(time.monotonic() - start, 3), **result}


def main(argv=None):
    parser = argparse.ArgumentParser(description="One harmless API connection request per provider; no evaluation data.")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    ledger_path = ROOT / ".local/stage1-api-connection/ledger.json"
    output = ROOT / "docs/stage1-api-connection-2026-10-26/results.json"
    if ledger_path.exists():
        print(json.dumps({"status": "RUN_ALREADY_RESERVED_OR_EXECUTED_NO_ADDITIONAL_REQUESTS", "saved_results": str(output)}))
        return 2
    keys = {provider: read_key(spec["env"]) for provider, spec in PROVIDERS.items()}
    report = {"time_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
              "scope": "CONNECTION_TEST_ONLY_NO_FULL_LABELING_NO_TEST_SET",
              "key_presence": {provider: bool(value) for provider, value in keys.items()},
              "test_budget_usd": TEST_BUDGET_USD, "max_output_tokens_per_request": OUTPUT_LIMIT,
              "automatic_retries": 0, "maximum_total_requests": 3, "results": [],
              "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
              "claude_credit_balance": None, "claude_credit_balance_status": "BILLING_PAGE_REQUIRES_USER_LOGIN",
              "price_basis": "2026-10-26 official standard text token rates; not a final invoice or balance query"}
    reserve = sum((1000 * spec["input_price"] + OUTPUT_LIMIT * spec["output_price"]) / 1_000_000 for spec in PROVIDERS.values())
    report["preflight_estimate_usd_with_1000_input_tokens_reserved_each"] = reserve
    if not all(keys.values()):
        report["status"] = "WAITING_FOR_ENVIRONMENT_KEYS_NO_REQUESTS_SENT"
    elif not args.execute:
        report["status"] = "READY_NO_REQUESTS_SENT"
    elif reserve > TEST_BUDGET_USD:
        report["status"] = "BUDGET_PREFLIGHT_BLOCKED"
    else:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with ledger_path.open("x", encoding="utf-8") as handle:
                json.dump({"scope": report["scope"], "attempted_providers": []}, handle)
        except FileExistsError:
            print(json.dumps({"status": "RUN_ALREADY_RESERVED_OR_EXECUTED_NO_ADDITIONAL_REQUESTS", "ledger": str(ledger_path)}))
            return 2
        attempted = []
        for provider, key in keys.items():
            attempted.append(provider)
            save_json(ledger_path, {"scope": report["scope"], "attempted_providers": attempted, "results": report["results"]})
            report["results"].append(send_once(provider, key))
            save_json(ledger_path, {"scope": report["scope"], "attempted_providers": attempted, "results": report["results"]})
            save_json(output, report)
        report["status"] = "ALL_THREE_SUCCEEDED" if all(item["status"] == "SUCCESS" for item in report["results"]) else "CONNECTION_TEST_FINISHED_WITH_FAILURES_NO_RETRY"
    report["total_attempts"] = sum(item["attempts"] for item in report["results"])
    report["successful_requests"] = sum(item["status"] == "SUCCESS" for item in report["results"])
    report["known_estimated_cost_usd"] = sum(item.get("estimated_standard_token_cost_usd") or 0 for item in report["results"])
    report["billing_cost_complete"] = bool(report["results"]) and all(item.get("estimated_standard_token_cost_usd") is not None for item in report["results"])
    serialized = json.dumps(report)
    if any(value and value in serialized for value in keys.values()):
        raise RuntimeError("Sensitive value detected; report was not saved")
    save_json(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in ("ALL_THREE_SUCCEEDED", "READY_NO_REQUESTS_SENT") else 2


if __name__ == "__main__":
    raise SystemExit(main())
