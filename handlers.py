"""Telegram bot handlers for private messages."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from database import Database, RecentJob
from job_parser import build_caption
from models import Job
from states import FilterStates

logger = logging.getLogger(__name__)

router = Router(name="private_handlers")
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)

BTN_LAST = "💼 Последние вакансии"
BTN_FILTER = "⚙️ Настроить фильтр"
BTN_ABOUT = "ℹ️ О боте"

TITLE_MAX_LEN = 36
VACANCY_CB_PREFIX = "vac:"
VACANCY_LIST_BACK = "vac_list:back"
FILTER_CAT_PREFIX = "flt:cat:"
FILTER_KW_PREFIX = "flt:kw:"
FILTER_BACK_CATEGORIES = "flt:back:categories"

FILTER_STACKS: dict[str, list[tuple[str, str]]] = {
    "backend": [
        ("Python", "python"),
        ("Java", "java"),
        ("PHP", "php"),
        ("Go", "go"),
        ("Node.js", "nodejs"),
        ("C#", "csharp"),
    ],
    "frontend": [
        ("JavaScript", "javascript"),
        ("TypeScript", "typescript"),
        ("React", "react"),
        ("Vue", "vue"),
        ("Angular", "angular"),
    ],
    "mobile": [
        ("Flutter", "flutter"),
        ("iOS (Swift)", "swift"),
        ("Android (Kotlin)", "kotlin"),
    ],
}

FILTER_SEARCH_KEYWORDS: dict[str, str] = {
    "python": "Python",
    "java": "Java",
    "php": "PHP",
    "go": "Go",
    "nodejs": "Node.js",
    "csharp": "C#",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "flutter": "Flutter",
    "swift": "Swift",
    "kotlin": "Kotlin",
}

LIST_PROMPT = "Выберите вакансию для просмотра:"

WELCOME_TEXT = (
    "👋 <b>Привет!</b>\n\n"
    "Я модульный Telegram-бот для рассылки IT-вакансий.\n\n"
    "Новые вакансии автоматически публикуются в нашей группе.\n"
    "Настройте персональный фильтр — и я буду присылать подходящие "
    "вакансии вам в личные сообщения."
)

ABOUT_TEXT = (
    "<b>О боте</b>\n\n"
    "🔍 Источник: модульный парсер вакансий (Generic Job Scraper Framework)\n"
    "👨‍💻 Фокус: IT-вакансии для разработчиков\n\n"
    "Бот периодически проверяет новые вакансии и отправляет их "
    "в Telegram-группу с описанием, зарплатой и ссылкой.\n\n"
    "⚙️ В разделе «Настроить фильтр» можно выбрать категорию стека "
    "или ввести своё ключевое слово — подходящие вакансии будут "
    "приходить в ЛС.\n\n"
    "Хэштеги: #jobs #it #developer #programming #hiring"
)

CUSTOM_FILTER_PROMPT = (
    "Пришлите мне ключевое слово (например: Django, Laravel, Unity, Senior). "
    "Я буду искать его в названии и описании вакансий."
)


def reply_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_LAST)],
            [KeyboardButton(text=BTN_FILTER), KeyboardButton(text=BTN_ABOUT)],
        ],
        resize_keyboard=True,
    )


def filter_categories_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🖥️ Backend", callback_data=f"{FILTER_CAT_PREFIX}backend")],
            [InlineKeyboardButton(text="🎨 Frontend", callback_data=f"{FILTER_CAT_PREFIX}frontend")],
            [InlineKeyboardButton(text="📱 Mobile", callback_data=f"{FILTER_CAT_PREFIX}mobile")],
            [
                InlineKeyboardButton(
                    text="🔍 Свой стек (Ввод текстом)",
                    callback_data=f"{FILTER_CAT_PREFIX}custom",
                )
            ],
        ]
    )


def filter_stack_keyboard(category: str) -> InlineKeyboardMarkup:
    stacks = FILTER_STACKS[category]
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"{FILTER_KW_PREFIX}{code}")]
        for label, code in stacks
    ]
    rows.append(
        [InlineKeyboardButton(text="🔙 Назад к категориям", callback_data=FILTER_BACK_CATEGORIES)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def filter_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к категориям", callback_data=FILTER_BACK_CATEGORIES)]
        ]
    )


def truncate_title(title: str, max_len: int = TITLE_MAX_LEN) -> str:
    if len(title) <= max_len:
        return title
    return title[: max_len - 1].rstrip() + "…"


def recent_to_job(item: RecentJob) -> Job:
    return Job(
        id=item.id,
        title=item.title,
        company=item.company,
        salary=item.salary,
        link=item.link,
        description=item.description,
    )


def jobs_inline_keyboard(recent: list[RecentJob]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=truncate_title(item.title),
                callback_data=f"{VACANCY_CB_PREFIX}{item.id}",
            )
        ]
        for item in recent
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def vacancy_detail_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться к списку", callback_data=VACANCY_LIST_BACK)]
        ]
    )


def filter_settings_text(current: str | None) -> str:
    filter_hint = f"\n\nТекущий фильтр: <b>{current}</b>" if current else ""
    return (
        "⚙️ <b>Настройка фильтра</b>\n\n"
        "Выберите категорию или введите свой стек. Бот будет присылать в ЛС "
        "только те вакансии, в названии или описании которых есть выбранное слово."
        f"{filter_hint}"
    )


async def show_vacancy_list(message_or_callback, db: Database) -> None:
    recent = await db.get_recent(limit=5)
    if not recent:
        text = (
            "Пока нет отправленных вакансий. Подождите первую рассылку "
            "или запустите `python test_db_fill.py` для тестовых данных."
        )
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.edit_text(text)
        else:
            await message_or_callback.answer(text)
        return

    markup = jobs_inline_keyboard(recent)
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(LIST_PROMPT, reply_markup=markup)
    else:
        await message_or_callback.answer(LIST_PROMPT, reply_markup=markup)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        WELCOME_TEXT,
        reply_markup=reply_main_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.message(F.text == BTN_ABOUT)
async def btn_about(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(ABOUT_TEXT, parse_mode=ParseMode.HTML)


@router.message(F.text == BTN_FILTER)
async def btn_filter(message: Message, db: Database, state: FSMContext) -> None:
    await state.clear()
    current = await db.get_user_filter(message.from_user.id)
    await message.answer(
        filter_settings_text(current),
        reply_markup=filter_categories_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.message(F.text == BTN_LAST)
async def btn_last_vacancies(message: Message, db: Database, state: FSMContext) -> None:
    await state.clear()
    await show_vacancy_list(message, db)


@router.message(StateFilter(FilterStates.waiting_for_keyword), F.text)
async def process_custom_keyword(message: Message, db: Database, state: FSMContext) -> None:
    if message.text in (BTN_LAST, BTN_FILTER, BTN_ABOUT):
        await state.clear()
        if message.text == BTN_LAST:
            await btn_last_vacancies(message, db, state)
        elif message.text == BTN_FILTER:
            await btn_filter(message, db, state)
        else:
            await btn_about(message, state)
        return

    keyword = (message.text or "").strip()
    if not keyword:
        await message.answer("Ключевое слово не может быть пустым. Попробуйте ещё раз.")
        return
    if len(keyword) > 64:
        await message.answer("Слишком длинное слово. Максимум 64 символа.")
        return

    await db.set_user_filter(message.from_user.id, keyword)
    await state.clear()
    await message.answer(
        f"✅ Фильтр <b>{keyword}</b> успешно установлен!\n\n"
        "Вы будете получать в личные сообщения новые вакансии, "
        "которые содержат это слово в названии или описании.",
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == VACANCY_LIST_BACK)
async def callback_back_to_list(callback: CallbackQuery, db: Database) -> None:
    if not callback.message:
        return

    await callback.answer()
    recent = await db.get_recent(limit=5)
    if not recent:
        await callback.message.edit_text(
            "Пока нет отправленных вакансий. Подождите первую рассылку.",
        )
        return

    await callback.message.edit_text(
        LIST_PROMPT,
        reply_markup=jobs_inline_keyboard(recent),
    )


@router.callback_query(F.data.startswith(VACANCY_CB_PREFIX))
async def callback_show_vacancy(callback: CallbackQuery, db: Database) -> None:
    if not callback.data or not callback.message:
        return

    job_id = callback.data.removeprefix(VACANCY_CB_PREFIX)
    item = await db.get_recent_by_id(job_id)

    if item is None:
        await callback.answer("Вакансия не найдена", show_alert=True)
        return

    await callback.answer()
    caption = build_caption(recent_to_job(item))

    await callback.message.edit_text(
        caption,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=vacancy_detail_keyboard(),
    )


@router.callback_query(F.data == FILTER_BACK_CATEGORIES)
async def callback_filter_back(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    if not callback.message or not callback.from_user:
        return

    await state.clear()
    await callback.answer()
    current = await db.get_user_filter(callback.from_user.id)
    await callback.message.edit_text(
        filter_settings_text(current),
        reply_markup=filter_categories_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith(FILTER_CAT_PREFIX))
async def callback_filter_category(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data or not callback.message:
        return

    category = callback.data.removeprefix(FILTER_CAT_PREFIX)

    if category == "custom":
        await callback.answer()
        await state.set_state(FilterStates.waiting_for_keyword)
        await callback.message.edit_text(
            CUSTOM_FILTER_PROMPT,
            reply_markup=filter_back_keyboard(),
        )
        return

    if category not in FILTER_STACKS:
        await callback.answer("Неизвестная категория", show_alert=True)
        return

    category_titles = {
        "backend": "Backend",
        "frontend": "Frontend",
        "mobile": "Mobile",
    }
    await callback.answer()
    await callback.message.edit_text(
        f"⚙️ <b>{category_titles[category]}</b>\n\nВыберите стек:",
        reply_markup=filter_stack_keyboard(category),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith(FILTER_KW_PREFIX))
async def callback_set_filter(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    if not callback.data or not callback.from_user or not callback.message:
        return

    code = callback.data.removeprefix(FILTER_KW_PREFIX)
    keyword = FILTER_SEARCH_KEYWORDS.get(code)

    if keyword is None:
        await callback.answer("Неизвестный фильтр", show_alert=True)
        return

    await state.clear()
    await db.set_user_filter(callback.from_user.id, keyword)
    await callback.answer(f"Фильтр сохранён: {keyword}")

    await callback.message.edit_text(
        f"✅ Фильтр <b>{keyword}</b> сохранён!\n\n"
        "Вы будете получать в личные сообщения новые вакансии, "
        "которые соответствуют выбранному стеку.",
        parse_mode=ParseMode.HTML,
    )
