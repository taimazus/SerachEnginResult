import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from rank_checker import normalize_domain


DEFAULT_DATABASE = Path(__file__).with_name("rank_tracker.sqlite3")


@contextmanager
def _connect():
    database_path = Path(os.environ.get("RANK_TRACKER_DB", DEFAULT_DATABASE))
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database():
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tracked_keywords (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                query TEXT NOT NULL,
                target_domain TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (project_id, query, target_domain)
            );
            CREATE TABLE IF NOT EXISTS rank_checks (
                id INTEGER PRIMARY KEY,
                tracked_keyword_id INTEGER NOT NULL
                    REFERENCES tracked_keywords(id) ON DELETE CASCADE,
                checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL CHECK (
                    status IN ('found', 'not_found', 'captcha', 'error')
                ),
                rank INTEGER,
                result_page INTEGER,
                message TEXT NOT NULL
            );
            """
        )


def create_project(name: str):
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("نام پروژه الزامی است.")
    try:
        with _connect() as connection:
            connection.execute(
                "INSERT INTO projects (name) VALUES (?)", (normalized_name,)
            )
    except sqlite3.IntegrityError as error:
        raise ValueError("این نام پروژه از قبل استفاده شده است.") from error


def get_projects():
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, name FROM projects ORDER BY name COLLATE NOCASE"
        ).fetchall()
        return [dict(row) for row in rows]


def add_keyword(project_id: int, query: str, target_domain: str):
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("عبارت جست‌وجو الزامی است.")
    normalized_domain = normalize_domain(target_domain)
    try:
        with _connect() as connection:
            connection.execute(
                """
                INSERT INTO tracked_keywords (project_id, query, target_domain)
                VALUES (?, ?, ?)
                """,
                (project_id, normalized_query, normalized_domain),
            )
    except sqlite3.IntegrityError as error:
        raise ValueError(
            "این عبارت و دامنه قبلاً در پروژه ثبت شده‌اند یا پروژه معتبر نیست."
        ) from error


def get_keywords(project_id: int):
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, query, target_domain
            FROM tracked_keywords
            WHERE project_id = ?
            ORDER BY query COLLATE NOCASE
            """,
            (project_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def save_check(keyword_id: int, result: dict):
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO rank_checks
                (tracked_keyword_id, status, rank, result_page, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                keyword_id,
                result["status"],
                result["rank"],
                result["result_page"],
                result["message"],
            ),
        )


def get_history(keyword_id: int, limit: int = 5):
    if limit < 1:
        raise ValueError("حد تاریخچه باید مثبت باشد.")
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT checked_at, status, rank, result_page, message
            FROM rank_checks
            WHERE tracked_keyword_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (keyword_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
