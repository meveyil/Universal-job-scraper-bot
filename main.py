"""Entry point: Telegram bot, scheduler, and job broadcasting."""

from __future__ import annotations

import asyncio
import logging
import sys

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, TelegramObject
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import handlers
from config import (
    BANNER_PATH,
    BOT_TOKEN,
    GROUP_ID,
    POLL_INTERVAL_MINUTES,
    setup_logging,
    validate_config,
)
from database import Database
from job_parser import build_caption, fetch_new_jobs, job_matches_keyword
from models import Job

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """Inject shared Database instance into handler context."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["db"] = self._db
        return await handler(event, data)


async def send_job_to_group(bot: Bot, db: Database, job: Job) -> None:
    """Send a single job posting as a photo with caption to the target group."""
    caption = build_caption(job)

    await bot.send_photo(
        chat_id=GROUP_ID,
        photo=FSInputFile(BANNER_PATH),
        caption=caption,
        parse_mode=ParseMode.HTML,
    )

    await db.mark_processed(job.id)
    await db.save_recent(job)
    logger.info("Sent job %s: %s", job.id, job.title)


async def send_job_to_subscribers(bot: Bot, db: Database, job: Job) -> None:
    """Send matching jobs to users who subscribed via personal filters."""
    subscribers = await db.get_all_user_filters()
    if not subscribers:
        return

    caption = build_caption(job)

    for user_id, keyword in subscribers:
        if not job_matches_keyword(job, keyword):
            continue

        try:
            await bot.send_photo(
                chat_id=user_id,
                photo=FSInputFile(BANNER_PATH),
                caption=caption,
                parse_mode=ParseMode.HTML,
            )
            logger.info(
                "Sent job %s to user %s (filter: %s)",
                job.id,
                user_id,
                keyword,
            )
            await asyncio.sleep(0.3)
        except TelegramForbiddenError:
            logger.warning("User %s blocked the bot, skipping DM", user_id)
        except TelegramBadRequest as exc:
            logger.warning(
                "Failed to send job %s to user %s: %s",
                job.id,
                user_id,
                exc,
            )


async def check_and_send_jobs(bot: Bot, db: Database) -> None:
    """Fetch new jobs from the active scraper and publish them."""
    logger.info("Starting job check...")
    try:
        jobs = await fetch_new_jobs(db)
    except Exception:
        logger.exception("Job fetch failed")
        return

    for job in jobs:
        try:
            await send_job_to_group(bot, db, job)
            await send_job_to_subscribers(bot, db, job)
            await asyncio.sleep(1)
        except Exception:
            logger.exception("Failed to send job %s", job.id)


async def main() -> None:
    setup_logging()
    validate_config()

    db = Database()
    await db.init()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DatabaseMiddleware(db))
    dp.include_router(handlers.router)

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        check_and_send_jobs,
        "interval",
        minutes=POLL_INTERVAL_MINUTES,
        args=[bot, db],
        id="job_poll",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("Scheduler started: every %s minutes", POLL_INTERVAL_MINUTES)

    asyncio.create_task(check_and_send_jobs(bot, db))

    try:
        logger.info("Bot polling started")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except ValueError as exc:
        logger.error("%s", exc)
        sys.exit(1)
