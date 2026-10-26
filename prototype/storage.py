from __future__ import annotations

import csv
import io
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .core import UserError, clean_text


class FeedbackStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, result TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
                    perspective_id TEXT NOT NULL, case_id TEXT NOT NULL, rating TEXT NOT NULL,
                    comment TEXT NOT NULL, tester TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_id, perspective_id, case_id));
            """)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def save(self, result, payload):
        if payload.get("consent") is not True:
            raise UserError("이 PC에 테스트 기록을 저장하는 데 동의해 주세요.")
        perspective_id = clean_text(payload.get("perspective_id", ""), 30)
        case_id = clean_text(payload.get("case_id", ""), 80)
        rating = payload.get("rating", "")
        if case_id:
            if not isinstance(rating, str) or rating not in {"useful", "partial", "irrelevant"}:
                raise UserError("유용함·부분적·무관 중 하나를 선택해 주세요.")
            if not any(branch["id"] == perspective_id and any(case["case_id"] == case_id for case in branch["cases"]) for branch in result["branches"]):
                raise UserError("현재 추천 결과에 없는 관점 또는 사례입니다.")
        elif perspective_id or rating != "overall":
            raise UserError("전체 의견 저장 요청이 올바르지 않습니다.")
        comment = clean_text(payload.get("comment", ""), 4000)
        tester = clean_text(payload.get("tester", ""), 80)
        if rating == "overall" and not comment:
            raise UserError("자유의견을 입력해 주세요.")
        with self.connect() as connection:
            connection.execute("INSERT OR IGNORE INTO sessions VALUES (?, ?)", (result["session_id"], json.dumps(result, ensure_ascii=False)))
            created_at = datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
            connection.execute("""INSERT INTO feedback (id,session_id,perspective_id,case_id,rating,comment,tester,created_at)
                VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(session_id,perspective_id,case_id)
                DO UPDATE SET rating=excluded.rating,comment=excluded.comment,tester=excluded.tester,created_at=excluded.created_at""",
                (uuid.uuid4().hex, result["session_id"], perspective_id, case_id, rating, comment, tester, created_at))
        return self.summary()

    def summary(self):
        with self.connect() as connection:
            rows = dict(connection.execute("SELECT rating,COUNT(*) FROM feedback GROUP BY rating").fetchall())
            sessions = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        return {"sessions": sessions, "ratings": rows, "total": sum(rows.values())}

    def export(self, format_name):
        with self.connect() as connection:
            connection.row_factory = sqlite3.Row
            sessions = [json.loads(row[0]) for row in connection.execute("SELECT result FROM sessions ORDER BY rowid")]
            feedback = [dict(row) for row in connection.execute("SELECT * FROM feedback ORDER BY created_at,id")]
        if format_name == "json":
            return json.dumps({"schema_version": 1, "kind": "USER_TEST_NOT_RESEARCH_GOLD", "sessions": sessions, "feedback": feedback}, ensure_ascii=False, indent=2).encode("utf-8")
        if format_name != "csv":
            raise UserError("JSON 또는 CSV를 선택해 주세요.")
        index = {row["session_id"]: row for row in sessions}
        target = io.StringIO(newline="")
        writer = csv.writer(target)
        writer.writerow(["평가ID", "세션ID", "시각(KST,+09:00)", "참여자별칭", "입력문제", "실행방식", "관점ID", "관점명", "사례ID", "평가", "자유의견", "버전"])
        ratings = {"useful": "유용함", "partial": "부분적", "irrelevant": "무관", "overall": "전체의견"}
        for row in feedback:
            session = index[row["session_id"]]
            branch_title = next((branch["title"] for branch in session["branches"] if branch["id"] == row["perspective_id"]), "전체")
            values = [row["id"], row["session_id"], row["created_at"], row["tester"], session["query"], session["provider"], row["perspective_id"], branch_title, row["case_id"], ratings[row["rating"]], row["comment"], session["corpus_version"]]
            writer.writerow(["'" + str(value) if str(value).lstrip().startswith(("=", "+", "-", "@")) else value for value in values])
        return target.getvalue().encode("utf-8-sig")
