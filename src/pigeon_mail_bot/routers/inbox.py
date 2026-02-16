from __future__ import annotations

from pathlib import Path

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import Command

from ..services.file_store import JsonlFileStore, WantToSendRecord, CanDeliverRecord, utc_now_iso
from ..settings import get_settings

router = Router()

WANT_STORE = JsonlFileStore(Path("data/want_to_send.jsonl"))
CAN_STORE = JsonlFileStore(Path("data/can_deliver.jsonl"))
SETTINGS = get_settings()

@router.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Ок, сбросила. Начнём заново.", reply_markup=main_menu_kb())


@router.message(F.text.casefold() == "сбросить")
async def cancel_btn(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Ок, сбросила. Начнём заново.", reply_markup=main_menu_kb())

# --- UI

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="хочу передать")],
            [KeyboardButton(text="могу передать")],
            [KeyboardButton(text="сбросить")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выбери действие",
    )


SIZE_LABELS = {
    "S": "документ",
    "M": "одна вещь/предмет",
    "L": "несколько вещей",
}

def size_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="S"), KeyboardButton(text="M"), KeyboardButton(text="L")]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выбери размер (S/M/L)",
    )

def size_prompt_text() -> str:
    return (
        "Выбери размер посылки:\n"
        "S — документ\n"
        "M — одна вещь/предмет\n"
        "L — несколько вещей"
    )

# --- FSM

class WantToSendFlow(StatesGroup):
    size = State()
    name = State()
    from_city = State()
    to_city = State()
    date = State()

class CanDeliverFlow(StatesGroup):
    size = State()
    name = State()
    from_city = State()
    to_city = State()
    date = State()

@router.message(F.text.startswith("/"))
async def any_command_resets(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Сбросила состояние. Выбери команду:", reply_markup=main_menu_kb())


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Привет! Выбери команду:",
        reply_markup=main_menu_kb(),
    )

@router.message(WantToSendFlow.size)
async def want_to_send_size(message: Message, state: FSMContext) -> None:
    choice = (message.text or "").strip().upper()
    if choice not in SIZE_LABELS:
        await message.answer("Выбери размер кнопками: S / M / L", reply_markup=size_kb())
        return

    await state.update_data(size=choice)
    await state.set_state(WantToSendFlow.name)
    await message.answer("Введи, пожалуйста, имя.", reply_markup=ReplyKeyboardRemove())


@router.message(CanDeliverFlow.size)
async def can_deliver_size(message: Message, state: FSMContext) -> None:
    choice = (message.text or "").strip().upper()
    if choice not in SIZE_LABELS:
        await message.answer("Выбери размер кнопками: S / M / L", reply_markup=size_kb())
        return

    await state.update_data(size=choice)
    await state.set_state(CanDeliverFlow.name)
    await message.answer("Введи, пожалуйста, имя.", reply_markup=ReplyKeyboardRemove())

@router.message(F.text.casefold() == "хочу передать")
async def want_to_send_begin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(WantToSendFlow.size)
    await message.answer(size_prompt_text(), reply_markup=size_kb())

@router.message(WantToSendFlow.name)
async def want_to_send_name(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer("Имя слишком короткое. Введи имя ещё раз.")
        return

    await state.update_data(name=text)
    await state.set_state(WantToSendFlow.from_city)
    await message.answer("Откуда передать? (например: Ларнака)")


@router.message(WantToSendFlow.from_city)
async def want_to_send_from(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer("Похоже, слишком коротко. Введи «откуда» ещё раз.")
        return

    await state.update_data(from_city=text)
    await state.set_state(WantToSendFlow.to_city)
    await message.answer("Куда передать? (например: Будапешт)")


@router.message(WantToSendFlow.to_city)
async def want_to_send_to(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer("Похоже, слишком коротко. Введи «куда» ещё раз.")
        return

    await state.update_data(to_city=text)
    await state.set_state(WantToSendFlow.date)
    await message.answer("Когда? (дата одним сообщением, например: 2026-02-01)")


@router.message(WantToSendFlow.date)
async def want_to_send_date(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 4:
        await message.answer("Дата выглядит странно. Введи дату ещё раз (например: 2026-02-01).")
        return

    data = await state.get_data()
    record = WantToSendRecord(
        user_id=message.from_user.id,
        username=message.from_user.username,
        name=str(data["name"]),
        from_city=str(data["from_city"]),
        to_city=str(data["to_city"]),
        date=text,
        size=str(data["size"]),
        created_at_utc=utc_now_iso(),
    )

    # 1. сохраняем
    WANT_STORE.append(record)

    # 2. формируем текст для канала
    size_desc = f'{record.size} — {SIZE_LABELS.get(record.size, "—")}'
    contact = f"@{record.username}" if record.username else "—"

    channel_text = (
        "📦 <b>ХОЧУ ПЕРЕДАТЬ</b>\n\n"
        f"📏 Размер: {size_desc}\n"
        f"👤 Имя: {record.name}\n"
        f"📍 Откуда: {record.from_city}\n"
        f"🎯 Куда: {record.to_city}\n"
        f"📅 Дата: {record.date}\n"
        f"🔗 Контакт: {contact}"
    )

    # 3. отправляем в канал
    await message.bot.send_message(
        chat_id=SETTINGS.channel_id,
        text=channel_text,
    )

    # 4. очищаем состояние
    await state.clear()

    # 5. отвечаем пользователю
    await message.answer(
        "Супер, заявка опубликована в канале ✅",
        reply_markup=main_menu_kb(),
    )



@router.message(F.text.casefold() == "могу передать")
async def can_deliver_begin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CanDeliverFlow.size)
    await message.answer(size_prompt_text(), reply_markup=size_kb())


@router.message(CanDeliverFlow.name)
async def can_deliver_name(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer("Имя слишком короткое. Введи имя ещё раз.")
        return

    await state.update_data(name=text)
    await state.set_state(CanDeliverFlow.from_city)
    await message.answer("Откуда летишь/едешь? (например: Ларнака)")


@router.message(CanDeliverFlow.from_city)
async def can_deliver_from(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer("Похоже, слишком коротко. Введи «откуда» ещё раз.")
        return

    await state.update_data(from_city=text)
    await state.set_state(CanDeliverFlow.to_city)
    await message.answer("Куда летишь/едешь? (например: Будапешт)")


@router.message(CanDeliverFlow.to_city)
async def can_deliver_to(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer("Похоже, слишком коротко. Введи «куда» ещё раз.")
        return

    await state.update_data(to_city=text)
    await state.set_state(CanDeliverFlow.date)
    await message.answer("Когда? (дата одним сообщением, например: 2026-02-01)")


@router.message(CanDeliverFlow.date)
async def can_deliver_date(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 4:
        await message.answer("Дата выглядит странно. Введи дату ещё раз (например: 2026-02-01).")
        return

    data = await state.get_data()
    record = CanDeliverRecord(
        user_id=message.from_user.id,
        username=message.from_user.username,
        name=str(data["name"]),
        from_city=str(data["from_city"]),
        to_city=str(data["to_city"]),
        date=text,
        size=str(data["size"]),
        created_at_utc=utc_now_iso(),
    )

    # 1) сохраняем в файл
    CAN_STORE.append(record)

    # 2) публикуем в канал
    contact = f"@{record.username}" if record.username else "—"
    size_desc = f'{record.size} — {SIZE_LABELS.get(record.size, "—")}'

    channel_text = (
        "✈️ <b>МОГУ ПЕРЕДАТЬ</b>\n\n"
        f"👤 Имя: {record.name}\n"
        f"📏 Размер: {size_desc}\n"
        f"📍 Откуда: {record.from_city}\n"
        f"🎯 Куда: {record.to_city}\n"
        f"📅 Дата: {record.date}\n"
        f"🔗 Контакт: {contact}"
    )

    await message.bot.send_message(
        chat_id=SETTINGS.channel_id,
        text=channel_text,
    )

    # 3) завершаем сценарий
    await state.clear()
    await message.answer(
        "Супер, заявка опубликована в канале ✅",
        reply_markup=main_menu_kb(),
    )


# fallback: если пользователь пишет что-то вне сценария
@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Используй /start, чтобы увидеть команды.", reply_markup=main_menu_kb())
