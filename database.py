"""SQLite storage for processed jobs, recent listings, and user filters."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import aiosqlite

from config import DATABASE_PATH
from models import Job

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RecentJob:
    id: str
    title: str
    company: str
    salary: str
    description: str
    link: str
    sent_at: datetime


class Database:
    """Async SQLite wrapper for job tracking and user subscriptions."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or str(DATABASE_PATH)

    async def init(self) -> None:
        """Create database tables if they do not exist."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_jobs (
                    job_id TEXT PRIMARY KEY,
                    processed_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS recent_jobs (
                    job_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    salary TEXT NOT NULL,
                    description TEXT NOT NULL,
                    link TEXT NOT NULL,
                    sent_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_filters (
                    user_id INTEGER PRIMARY KEY,
                    keyword TEXT NOT NULL
                )
                """
            )
            await db.commit()
        logger.info("Database initialized at %s", self._db_path)

    async def is_processed(self, job_id: str) -> bool:
        """Check whether a job has already been published."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM processed_jobs WHERE job_id = ?",
                (job_id,),
            )
            row = await cursor.fetchone()
            return row is not None

    async def mark_processed(self, job_id: str) -> None:
        """Mark a job as processed to prevent duplicate broadcasts."""
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT OR IGNORE INTO processed_jobs (job_id, processed_at)
                VALUES (?, ?)
                """,
                (job_id, now),
            )
            await db.commit()

    async def save_recent(self, job: Job) -> None:
        """Persist a job in the recent listings cache."""
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO recent_jobs
                (job_id, title, company, salary, description, link, sent_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (job.id, job.title, job.company, job.salary, job.description, job.link, now),
            )
            await db.execute(
                """
                DELETE FROM recent_jobs
                WHERE job_id IN (
                    SELECT job_id FROM recent_jobs
                    ORDER BY sent_at DESC
                    LIMIT -1 OFFSET 50
                )
                """
            )
            await db.commit()

    async def get_recent(self, limit: int = 5) -> list[RecentJob]:
        """Return the most recently published jobs."""
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT job_id, title, company, salary, description, link, sent_at
                FROM recent_jobs
                ORDER BY sent_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()

        return [
            RecentJob(
                id=row["job_id"],
                title=row["title"],
                company=row["company"],
                salary=row["salary"],
                description=row["description"],
                link=row["link"],
                sent_at=datetime.fromisoformat(row["sent_at"]),
            )
            for row in rows
        ]

    async def get_recent_by_id(self, job_id: str) -> RecentJob | None:
        """Return a single recent job by its identifier."""
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT job_id, title, company, salary, description, link, sent_at
                FROM recent_jobs
                WHERE job_id = ?
                """,
                (job_id,),
            )
            row = await cursor.fetchone()

        if row is None:
            return None

        return RecentJob(
            id=row["job_id"],
            title=row["title"],
            company=row["company"],
            salary=row["salary"],
            description=row["description"],
            link=row["link"],
            sent_at=datetime.fromisoformat(row["sent_at"]),
        )

    async def set_user_filter(self, user_id: int, keyword: str) -> None:
        """Save or update a user's personal job filter keyword."""
        keyword = keyword.strip()
        if not keyword:
            raise ValueError("Filter keyword cannot be empty")

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO user_filters (user_id, keyword)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET keyword = excluded.keyword
                """,
                (user_id, keyword),
            )
            await db.commit()

    async def get_user_filter(self, user_id: int) -> str | None:
        """Return the filter keyword for a user, if configured."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT keyword FROM user_filters WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def get_all_user_filters(self) -> list[tuple[int, str]]:
        """Return all user filter subscriptions."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute("SELECT user_id, keyword FROM user_filters")
            rows = await cursor.fetchall()
        return [(row[0], row[1]) for row in rows]
