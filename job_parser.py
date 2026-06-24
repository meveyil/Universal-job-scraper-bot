"""Standard job caption formatting and scraper orchestration."""

from __future__ import annotations

import html
import logging
import re

from config import CAPTION_LIMIT, HASHTAGS
from database import Database
from models import Job
from scrapers.registry import get_scraper

logger = logging.getLogger(__name__)

TAG_RE = re.compile(r"<[^>]+>")


def _visible_length(text: str) -> int:
    """Approximate visible caption length without HTML tags."""
    return len(TAG_RE.sub("", text))


def build_caption(job: Job) -> str:
    """Build an HTML Telegram caption truncated to platform limits."""
    title = html.escape(job.title)
    salary = html.escape(job.salary)
    company = html.escape(job.company)
    description = html.escape(job.description)
    link = html.escape(job.link, quote=True)

    header = (
        f"<b>{title}</b>\n\n"
        f"💰 <b>Salary:</b> {salary}\n"
        f"🏢 <b>Company:</b> {company}\n\n"
    )
    footer = f'\n\n<a href="{link}">View job</a>\n\n{HASHTAGS}'

    max_description_len = CAPTION_LIMIT - _visible_length(header) - _visible_length(footer)
    if max_description_len < 0:
        max_description_len = 0

    if len(description) > max_description_len:
        if max_description_len <= 3:
            description = "..."
        else:
            description = description[: max_description_len - 3].rstrip() + "..."

    return f"{header}{description}{footer}"


def job_matches_keyword(job: Job, keyword: str) -> bool:
    """Return True if the keyword appears in the job title or description."""
    keyword = keyword.strip()
    if not keyword:
        return False

    if keyword.casefold() in {"any", "all", "любые"}:
        return True

    haystack = f"{job.title} {job.description}".casefold()
    return keyword.casefold() in haystack


async def fetch_new_jobs(db: Database) -> list[Job]:
    """
    Fetch jobs from the configured scraper and return only unprocessed items.

    The active scraper is selected via the SCRAPER_SOURCE environment variable.
    """
    scraper = get_scraper()
    jobs = await scraper.fetch_jobs()
    new_jobs: list[Job] = []

    for job in jobs:
        if await db.is_processed(job.id):
            continue
        new_jobs.append(job)

    logger.info(
        "Scraper '%s' returned %s jobs (%s new)",
        scraper.name,
        len(jobs),
        len(new_jobs),
    )
    return new_jobs
