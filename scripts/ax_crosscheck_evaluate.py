"""Submit one frozen evaluation request and write an encrypted receipt."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

MODELS = {
    "claude": ("claude-sonnet-5-5", "ANTHROPIC_API_KEY"),
    "gemini": ("gemini-3.1-pro-preview", "GEMINI_API_KEY"),
    "deepseek": ("deepseek-v4-pro", "DEEPSEEK_API_KEY"),
}

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def prepare(provider, model, key, original):
    system, payload, schema = (original[k] for k in ("system", "payload", "schema"))
    data = original["body"]["input"]
    assert json.loads(data) == payload and original["body"]["instructions"] == system
    cap = original["body"]["max_output_tokens"]
    if provider == "claude":
        return "https://api.anthropic.com/v1/messages", {
            "x-api-key": key, "anthropic-version": "2023-06-01",
        }, {
            "model": model, "system": system, "max_tokens": cap,
            "messages": [{"role": "user", "content": data}],
            "output_config": {"format": {"type": "json_schema", "schema": schema}},
        }
    if provider == "gemini":
        return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", {
            "x-goog-api-key": key,
        }, {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": data}]}],
            "generationConfig": {"maxOutputTokens": cap, "responseMimeType": "application/json",
                                 "responseJsonSchema": schema},
        }
    return "https://api.deepseek.com/chat/completions", {"Authorization": f"Bearer {key}"}, {
        "model": model, "max_tokens": cap, "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": data + "\n\nReturn JSON matching this output schema:\n" +
                      json.dumps(schema, ensure_ascii=False)}],
    }

def extract(provider, raw):
    if provider == "claude":
        return raw["model"], raw["stop_reason"], "end_turn", raw["usage"], "".join(
            x["text"] for x in raw["content"] if x["type"] == "text")
    if provider == "gemini":
        candidate = raw["candidates"][0]
        return raw["modelVersion"], candidate["finishReason"], "STOP", raw["usageMetadata"], "".join(
            x.get("text", "") for x in candidate["content"]["parts"] if not x.get("thought"))
    choice = raw["choices"][0]
    return raw["model"], choice["finish_reason"], "stop", raw["usage"], choice["message"]["content"]

def validate(value):
    if set(value) != {"rows"}:
        raise ValueError("invalid_object")
    rows = value["rows"]
    if len(rows) != 28 or {r["position"] for r in rows} != set(range(28)):
        raise ValueError("position_coverage")
    for r in rows:
        if set(r) != {"position", "grade", "brief_bridge", "assumption", "perspectives"}:
            raise ValueError("response_fields")
        if type(r["position"]) is not int or type(r["grade"]) is not int or not 0 <= r["grade"] <= 3:
            raise ValueError("invalid_grade_or_position")
        if not isinstance(r["brief_bridge"], str) or not isinstance(r["assumption"], str):
            raise ValueError("invalid_explanation")
        views = r["perspectives"]
        if not isinstance(views, list) or len(views) != len(set(views)) or not set(views) <= {"P01","P02","P03","P04"}:
            raise ValueError("invalid_perspectives")

def main():
    provider, frozen, expected, cert = sys.argv[1:]
    frozen_bytes = Path(frozen).read_bytes()
    assert hashlib.sha256(frozen_bytes).hexdigest() == expected
    original = json.loads(frozen_bytes)
    model, secret_name = MODELS[provider]
    key = os.environ.pop(secret_name, "")
    if not key:
        raise SystemExit("missing_provider_secret")
    url, headers, body = prepare(provider, model, key, original)
    request = urllib.request.Request(url, json.dumps(body, ensure_ascii=False).encode(),
                                    {"Content-Type":"application/json", **headers}, method="POST")
    start = time.monotonic()
    receipt = {"provider": provider, "requested_model": model, "request_id": original["id"],
               "frozen_sha256": expected, "started_at": utc(), "github_run": os.environ.get("GITHUB_RUN_ID"),
               "github_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"), "body": body}
    try:
        with urllib.request.urlopen(request, timeout=270) as response:
            receipt["headers"] = {k: v for k, v in response.headers.items()
                                  if "rate" in k.lower() or k.lower() in ("retry-after", "request-id", "x-request-id")}
            receipt["raw"] = json.load(response)
        returned, finish, expected_finish, usage, content = extract(provider, receipt["raw"])
        receipt.update(returned_model=returned, finish=finish, usage=usage)
        if finish != expected_finish:
            raise ValueError("unexpected_finish")
        parsed = json.loads(content)
        validate(parsed)
        receipt.update(status="valid", parsed=parsed)
    except urllib.error.HTTPError as exc:
        receipt.update(status=f"http_{exc.code}", detail=exc.read(65536).decode(errors="replace"))
    except Exception as exc:
        receipt.update(status="invalid_response" if "raw" in receipt else "delivery_unknown",
                       detail=type(exc).__name__ + ": " + str(exc))
    receipt.update(duration_seconds=round(time.monotonic()-start, 3), finished_at=utc())
    path = Path(f"{provider}-{original['id']}.cms")
    subprocess.run(["openssl", "cms", "-encrypt", "-aes-256-gcm", "-binary", "-outform",
                    "DER", "-out", str(path), cert], input=json.dumps(receipt, ensure_ascii=False).encode(), check=True)
    print(f"{provider} {original['id']} status={receipt['status']} encrypted_receipt={path.name}")

if __name__ == "__main__":
    main()
