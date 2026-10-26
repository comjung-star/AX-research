from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import secrets
import socket
import threading
import webbrowser
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .core import Engine, ROOT, UserError, clean_text
from .credentials import WindowsCredentialStore
from .storage import FeedbackStore
from .settings import load_local_env


class PrototypeHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = os.name != "nt"

    def server_bind(self):
        if os.name == "nt":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class Application:
    def __init__(self, storage_path=None, credential_store=None, corpus_profile="frozen"):
        self.engine = Engine(profile=corpus_profile)
        self.store = FeedbackStore(Path(storage_path or os.getenv("AX_FEEDBACK_DB", str(ROOT / ".local/ax-prototype/feedback.sqlite3"))))
        self.token = secrets.token_urlsafe(32)
        self.sessions = OrderedDict()
        self.session_lock = threading.Lock()
        self.credentials = credential_store or WindowsCredentialStore()
        self.connection = {"verified": False, "remembered": False}
        if storage_path is None and not os.getenv("OPENAI_API_KEY"):
            try:
                saved = self.credentials.read()
                if saved and isinstance(saved.get("api_key"), str) and isinstance(saved.get("model"), str):
                    os.environ["OPENAI_API_KEY"] = saved["api_key"]
                    os.environ["AX_LLM_MODEL"] = saved["model"]
                    self.connection["remembered"] = True
            except Exception:
                pass

    def bootstrap(self):
        return {**self.engine.info(), "token": self.token, "feedback": self.store.summary(),
                "connection": self.connection, "secure_remember_supported": self.credentials.supported,
                "default_mode": "live" if os.getenv("OPENAI_API_KEY") else "demo"}

    def connect_api(self, payload):
        api_key = payload.get("api_key", "")
        if not isinstance(api_key, str) or len(api_key) > 1024:
            raise UserError("API키 입력 형식을 확인해 주세요.")
        api_key = api_key.strip() or os.getenv("OPENAI_API_KEY", "")
        if not re.fullmatch(r"sk-[A-Za-z0-9_-]{12,}", api_key):
            raise UserError("OpenAI API키를 입력해 주세요. 키는 채팅이나 업무문제 입력란에 붙이지 마세요.")
        model = clean_text(payload.get("model", os.getenv("AX_LLM_MODEL", "gpt-6-luna")), 128)
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}", model):
            raise UserError("모델 이름을 확인해 주세요.")
        remember = payload.get("remember", False)
        if type(remember) is not bool or (remember and not self.credentials.supported):
            raise UserError("이 환경에서는 Windows 보안 저장을 사용할 수 없습니다.")
        if not self.engine.lock.acquire(blocking=False):
            raise UserError("분석 중에는 연결을 바꿀 수 없습니다. 완료 후 다시 시도해 주세요.")
        try:
            branches = self.engine._generate_perspectives("고객 문의가 늘어 반복 질문에 시간이 많이 들고 복잡한 문의의 대응이 늦어집니다.", api_key=api_key, model=model)
            if remember:
                try:
                    self.credentials.save(api_key, model)
                except Exception:
                    raise UserError("Windows 보안 저장에 실패했습니다. 기억하기를 끄고 연결하거나 Windows 계정을 확인해 주세요.") from None
            else:
                try:
                    self.credentials.delete()
                except Exception:
                    raise UserError("이전 저장 키를 정리하지 못했습니다. Windows 자격 증명 관리자를 확인해 주세요.") from None
            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["AX_LLM_MODEL"] = model
            self.connection = {"verified": True, "remembered": remember, "test_perspective_count": len(branches),
                               "evidence": self.engine.last_llm_evidence}
            return self.bootstrap()
        finally:
            self.engine.lock.release()

    def disconnect_api(self):
        if not self.engine.lock.acquire(blocking=False):
            raise UserError("분석이 끝난 뒤 연결을 해제해 주세요.")
        try:
            self.credentials.delete()
            os.environ.pop("OPENAI_API_KEY", None)
            self.engine.last_llm_evidence = None
            self.connection = {"verified": False, "remembered": False}
            return self.bootstrap()
        finally:
            self.engine.lock.release()

    def remember(self, result):
        with self.session_lock:
            self.sessions[result["session_id"]] = result
            while len(self.sessions) > 200:
                self.sessions.popitem(last=False)


def make_handler(application):
    class Handler(BaseHTTPRequestHandler):
        server_version = "AXPrototype/1.0"

        def log_message(self, format_string, *args):
            pass

        def discard_request_body(self):
            try:
                length = min(max(int(self.headers.get("Content-Length", "0")), 0), 65536)
            except ValueError:
                return
            previous_timeout = self.connection.gettimeout()
            try:
                self.connection.settimeout(1)
                if length:
                    self.rfile.read(length)
            except OSError:
                pass
            finally:
                self.connection.settimeout(previous_timeout)

        def trusted_request(self, mutation=False):
            port = self.server.server_address[1]
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            if self.headers.get("Host") not in hosts:
                return False
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://{host}" for host in hosts}:
                return False
            return not mutation or hmac.compare_digest(self.headers.get("X-AX-Token", ""), application.token)

        def respond(self, status, payload, content_type="application/json; charset=utf-8", filename=None):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if not isinstance(payload, bytes) else payload
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            if not self.trusted_request():
                return self.respond(403, {"error": "이 PC의 실행 화면에서만 접근할 수 있습니다."})
            path = urlsplit(self.path).path
            if path == "/api/health":
                return self.respond(200, {"status": "ok", "app": "ax-prototype", "cases": len(application.engine.case_ids), "records": len(application.engine.cases), "corpus_version": application.engine.corpus_version})
            if path == "/api/bootstrap":
                return self.respond(200, application.bootstrap())
            if path in {"/api/export.json", "/api/export.csv"}:
                if not self.trusted_request(mutation=True):
                    return self.respond(403, {"error": "화면의 내보내기 버튼을 사용해 주세요."})
                format_name = path.rsplit(".", 1)[1]
                return self.respond(200, application.store.export(format_name), "application/json; charset=utf-8" if format_name == "json" else "text/csv; charset=utf-8", f"ax-user-test.{format_name}")
            files = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css", "/research.js": "research.js", "/research.css": "research.css"}
            if path in files:
                filename = files[path]
                content_type = {"html": "text/html", "js": "text/javascript", "css": "text/css"}[filename.rsplit(".", 1)[1]]
                return self.respond(200, (ROOT / "prototype/web" / filename).read_bytes(), content_type + "; charset=utf-8")
            self.respond(404, {"error": "페이지를 찾을 수 없습니다."})

        def do_POST(self):
            if not self.trusted_request(mutation=True):
                self.discard_request_body()
                return self.respond(403, {"error": "현재 실행 화면에서 다시 시도해 주세요."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 32768:
                    self.discard_request_body()
                    return self.respond(413, {"error": "요청 내용이 너무 큽니다."})
                body = self.rfile.read(length)
                if self.headers.get("Content-Type", "").split(";", 1)[0] != "application/json":
                    return self.respond(415, {"error": "JSON 요청이 필요합니다."})
                payload = json.loads(body.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise UserError("올바른 입력 형식이 아닙니다.")
                path = urlsplit(self.path).path
                if path == "/api/connection":
                    return self.respond(200, application.connect_api(payload))
                if path == "/api/disconnect":
                    return self.respond(200, application.disconnect_api())
                if path == "/api/recommend":
                    result = application.engine.recommend(payload)
                    application.remember(result)
                    return self.respond(200, result)
                if path == "/api/feedback":
                    session_id = payload.get("session_id")
                    if not isinstance(session_id, str):
                        raise UserError("분석을 실행한 뒤 평가해 주세요.")
                    with application.session_lock:
                        result = application.sessions.get(session_id)
                    if result is None:
                        raise UserError("실행 기록이 만료되었습니다. 사례를 다시 찾아 주세요.")
                    return self.respond(200, application.store.save(result, payload))
                if path == "/api/shutdown":
                    self.respond(200, {"status": "stopped"})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                return self.respond(404, {"error": "지원하지 않는 요청입니다."})
            except (UserError, UnicodeError, json.JSONDecodeError, ValueError) as error:
                message = str(error) if isinstance(error, UserError) else "입력 형식을 확인해 주세요."
                self.respond(400, {"error": message})
            except Exception:
                self.respond(500, {"error": "처리를 완료하지 못했습니다. 다시 시도하거나 실행 안내를 확인해 주세요."})

    return Handler


def main():
    load_local_env()
    parser = argparse.ArgumentParser(description="AX 사례 추천 로컬 프로토타입")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    inclusive_ready = all((ROOT / "data/v2_5" / filename).is_file() for filename in ("main_cases_v2_5.json", "inclusive_bge_m3.npz", "index_manifest.json"))
    parser.add_argument("--corpus", choices=["inclusive", "active", "frozen"], default="inclusive" if inclusive_ready else "active")
    args = parser.parse_args()
    application = Application(corpus_profile=args.corpus)
    try:
        server = PrototypeHTTPServer(("127.0.0.1", args.port), make_handler(application))
    except OSError:
        import urllib.request
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/api/health", timeout=2) as response:
                existing = json.load(response)
            if existing.get("app") == "ax-prototype":
                if not args.no_browser:
                    webbrowser.open(f"http://127.0.0.1:{args.port}")
                return
        except Exception:
            pass
        server = PrototypeHTTPServer(("127.0.0.1", 0), make_handler(application))
    url = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"AX prototype ready: {url}", flush=True)
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
