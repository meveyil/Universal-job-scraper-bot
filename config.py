"""Application configuration loaded from environment variables."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
GROUP_ID: int = int(os.getenv("GROUP_ID", "0") or "0")
BANNER_PATH: Path = Path(os.getenv("BANNER_PATH", "banner.jpg"))
SCRAPER_SOURCE: str = os.getenv("SCRAPER_SOURCE", "mock").strip().lower()
POLL_INTERVAL_MINUTES: int = int(os.getenv("POLL_INTERVAL_MINUTES", "15") or "15")

DATABASE_PATH: Path = BASE_DIR / "jobs.db"

CAPTION_LIMIT = 1024
HASHTAGS = "#jobs #it #developer #programming #hiring"

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger for the application."""
    logging.basicConfig(level=level, format=LOG_FORMAT)


def validate_config() -> None:
    """Raise ValueError if required settings are missing or invalid."""
    errors: list[str] = []

    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is not set")
    if GROUP_ID == 0:
        errors.append("GROUP_ID is not set or invalid")
    if not SCRAPER_SOURCE:
        errors.append("SCRAPER_SOURCE is not set")
    if not BANNER_PATH.exists():
        errors.append(f"BANNER_PATH file not found: {BANNER_PATH}")

    if errors:
        raise ValueError("Configuration errors:\n- " + "\n- ".join(errors))
