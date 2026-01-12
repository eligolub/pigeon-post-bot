from __future__ import annotations

from pathlib import Path

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from ..services.file_store import JsonlFileStore, WantToSendRecord, utc_now_iso
from ..settings import get_settings

router = Router()

STORE = JsonlFileStore(Path("data/want_to_send.jsonl"))
SETTINGS = get_settings()


# --- UI

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="хочу передать")],
            [KeyboardButton(text="могу передать")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выбери действие",
    )


# --- FSM

class WantToSendFlow(StatesGroup):
    name = State()
    route = State()
    date = State()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Привет! Выбери команду:",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text.casefold() == "хочу передать")
async def want_to_send_begin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(WantToSendFlow.name)
    await message.answer(
        "Введи, пожалуйста, имя.",
        reply_markup=ReplyKeyboardRemove(),  # убираем меню, чтобы не мешало вводу
    )


@router.message(WantToSendFlow.name)
async def want_to_send_name(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer("Имя слишком короткое. Введи имя ещё раз.")
        return

    await state.update_data(name=text)
    await state.set_state(WantToSendFlow.route)
    await message.answer("Откуда и куда? (например: Ларнака → Будапешт)")


@router.message(WantToSendFlow.route)
async def want_to_send_route(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 5:
        await message.answer("Похоже, маршрута мало. Напиши 'откуда → куда' одним сообщением.")
        return

    await state.update_data(route=text)
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
        route=str(data["route"]),
        date=text,
        created_at_utc=utc_now_iso(),
    )

    # 1. сохраняем
    STORE.append_want_to_send(record)

    # 2. формируем текст для канала
    channel_text = (
        "📦 <b>ХОЧУ ПЕРЕДАТЬ</b>\n\n"
        f"👤 Имя: {record.name}\n"
        f"✈️ Маршрут: {record.route}\n"
        f"📅 Дата: {record.date}\n"
        f"🔗 Контакт: @{record.username}" if record.username else "—"
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
async def can_deliver_stub(message: Message) -> None:
    await message.answer(
        "Пока это заглушка. Следующим шагом сделаем такой же сценарий и публикацию в канал.",
        reply_markup=main_menu_kb(),
    )


# fallback: если пользователь пишет что-то вне сценария
@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Используй /start, чтобы увидеть команды.", reply_markup=main_menu_kb())
