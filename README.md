# Universal Telegram Job Scraper Bot Framework

A modular, async Telegram bot framework for collecting job postings from pluggable sources and broadcasting them to a group channel and subscribed users.

Built with **aiogram 3.x**, **asyncio**, **APScheduler**, and **SQLite**.

---

## Description

This project is a **Generic Job Scraper Bot Framework**. Instead of being tied to a single job board, it uses a scraper plugin architecture:

- **`mock`** — built-in demo dataset for offline development (default)
- **`html`** — skeleton for HTML-based job boards (extend with your own parser)
- **Custom scrapers** — add new modules by implementing `BaseJobScraper`

Core features:

- Scheduled job polling via APScheduler
- Duplicate detection with SQLite
- Group broadcasts with banner image + HTML caption
- Private-message UX: recent jobs browser, filter categories, custom keyword subscriptions
- Personal DM notifications based on user filters

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  main.py    │────▶│ job_parser   │────▶│ scrapers/       │
│  scheduler  │     │ orchestrator │     │ registry        │
└─────────────┘     └──────────────┘     └────────┬────────┘
       │                    │                      │
       ▼                    ▼                      ▼
 handlers.py          models.Job            BaseJobScraper
       │                    │                 ├─ mock.py
       ▼                    ▼                 ├─ html_scraper.py
  database.py          build_caption          └─ your_scraper.py
```

### Standard job model

Every scraper must return `Job` objects with these fields:

| Field         | Type  | Description              |
|---------------|-------|--------------------------|
| `id`          | str   | Unique job identifier    |
| `title`       | str   | Job title                |
| `company`     | str   | Company name             |
| `salary`      | str   | Salary text (or "N/A")   |
| `link`        | str   | URL to the job posting   |
| `description` | str   | Short job description    |

### Adding a custom scraper

1. Create `scrapers/my_site.py`:

```python
from models import Job
from scrapers.base import BaseJobScraper


class MySiteScraper(BaseJobScraper):
    name = "mysite"

    async def fetch_jobs(self) -> list[Job]:
        # Fetch and parse your source, then return normalized Job objects.
        return [
            Job(
                id="123",
                title="Backend Developer",
                company="Example Corp",
                salary="Not specified",
                link="https://example.com/jobs/123",
                description="Python, FastAPI, PostgreSQL.",
            )
        ]
```

2. Register it in `scrapers/registry.py`:

```python
from scrapers.my_site import MySiteScraper

SCRAPER_REGISTRY = {
    "mock": MockJobScraper,
    "html": HtmlJobScraper,
    "mysite": MySiteScraper,
}
```

3. Set in `.env`:

```env
SCRAPER_SOURCE=mysite
```

---

## Installation & Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/meveyil/Universal-job-scraper-bot.git
cd Universal-job-scraper-bot
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Edit `.env` and fill in your values (see below).

### 5. Add a banner image

Place a JPEG/PNG file (e.g. `banner.jpg`) in the project root, or update `BANNER_PATH` in `.env`.

### 6. Run the bot

```bash
python main.py
```

### Optional test scripts

```bash
python test_db_fill.py   # seed recent jobs for PM UX testing
python test_send.py      # send one test job to the group
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable                | Required | Description                                      | Example                          |
|-------------------------|----------|--------------------------------------------------|----------------------------------|
| `BOT_TOKEN`             | Yes      | Telegram bot token from [@BotFather](https://t.me/BotFather) | `your_telegram_bot_token_here` |
| `GROUP_ID`              | Yes      | Target Telegram group chat ID (negative for groups) | `your_telegram_group_id_here` |
| `BANNER_PATH`           | Yes      | Path to the broadcast banner image               | `banner.jpg`                     |
| `SCRAPER_SOURCE`        | Yes      | Active scraper module key (`mock`, `html`, …)    | `mock`                           |
| `POLL_INTERVAL_MINUTES` | No       | Polling interval in minutes (default: `15`)      | `15`                             |

Example `.env`:

```env
BOT_TOKEN=your_telegram_bot_token_here
GROUP_ID=your_telegram_group_id_here
BANNER_PATH=banner.jpg
SCRAPER_SOURCE=mock
POLL_INTERVAL_MINUTES=15
```

> **Security:** Never commit `.env` or database files. They are listed in `.gitignore`.

---

## Project Structure

```
.
├── main.py              # Bot entry point + scheduler
├── config.py            # Environment configuration
├── models.py            # Job dataclass
├── job_parser.py        # Caption builder + fetch orchestration
├── database.py          # SQLite persistence
├── handlers.py          # Telegram private-message handlers
├── states.py            # FSM states
├── scrapers/            # Pluggable job source modules
│   ├── base.py
│   ├── mock.py
│   ├── html_scraper.py
│   └── registry.py
├── test_send.py         # Manual group send test
├── test_db_fill.py      # Manual DB seed for UI testing
├── requirements.txt
└── .env.example
```

---

## Tech Stack

- Python 3.11+
- [aiogram](https://docs.aiogram.dev/) 3.x
- [aiohttp](https://docs.aiohttp.org/)
- [APScheduler](https://apscheduler.readthedocs.io/)
- [aiosqlite](https://github.com/omnilib/aiosqlite)
- [python-dotenv](https://github.com/theskumar/python-dotenv)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
