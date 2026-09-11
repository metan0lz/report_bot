import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import logging
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=TOKEN)
dp = Dispatcher()

SAVED_FILE = "saved_values.json"


def load_saved():
    if os.path.exists(SAVED_FILE):
        try:
            with open(SAVED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_saved(data):
    try:
        with open(SAVED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Ошибка при сохранении файла: %s", e)


SAVED_VALUES = load_saved()


class ReportForm(StatesGroup):
    date = State()
    time = State()
    operator = State()
    engineer = State()
    direction = State()
    departure = State()
    drone_type = State()
    control = State()
    video_link = State()
    sparka = State()
    warhead = State()
    fuze_type = State()
    range_ = State()
    task = State()
    result = State()
    clarification = State()
    coord_x = State()
    coord_y = State()
    return_ = State()
    video_ = State()


FIELDS = [
    ("date", "📅 Дата"),
    ("time", "⏰ Время"),
    ("operator", "👤 Оператор"),
    ("engineer", "🔧 Инженер"),
    ("direction", "🧭 Направление"),
    ("departure", "✈️ Вылет"),
    ("drone_type", "🛩️ Тип дрона"),
    ("control", "🎮 Управление"),
    ("video_link", "📡 Видео (ссылка/описание)"),
    ("sparka", "🔗 Спарка"),
    ("warhead", "💥 Боевая часть"),
    ("fuze_type", "🧨 Тип взрывателя"),
    ("range_", "📏 Дальность"),
    ("task", "🎯 Задача"),
    ("result", "✅ Результат"),
    ("clarification", "📝 Уточнение"),
    ("coord_x", "📍 Координата X"),
    ("coord_y", "📍 Координата Y"),
    ("return_", "↩️ Возврат"),
    ("video_", "🎥 Видео (итоговое)"),
]

FIELDS_MAP = {name: label for name, label in FIELDS}


def get_next_field(current_name: str):
    for i, (name, _) in enumerate(FIELDS):
        if name == current_name:
            if i + 1 < len(FIELDS):
                return FIELDS[i + 1]
            return None
    return None


def make_keyboard(field_name: str):
    rows = []
    saved = SAVED_VALUES.get(field_name, [])

    for i in range(0, len(saved), 2):
        row = []
        for val in saved[i:i + 2]:
            display = val[:35] + "…" if len(val) > 35 else val
            row.append(InlineKeyboardButton(
                text=display,
                callback_data=f"sel:{field_name}:{val[:50]}"
            ))
        rows.append(row)

    rows.append([InlineKeyboardButton(text="✏️ Ввести вручную", callback_data=f"manual:{field_name}")])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


def add_saved_value(field_name: str, value: str):
    if field_name not in SAVED_VALUES:
        SAVED_VALUES[field_name] = []
    if value not in SAVED_VALUES[field_name]:
        SAVED_VALUES[field_name].append(value)
        SAVED_VALUES[field_name] = SAVED_VALUES[field_name][-6:]
    save_saved(SAVED_VALUES)


async def finish_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    operator = data.get("operator", "-")

    report = (
        f"📋 Расчёт ({operator}):\n"
        f"Дата: {data.get('date', '-')}\n"
        f"Время: {data.get('time', '-')}\n"
        f"Оператор: {operator}\n"
        f"Инженер: {data.get('engineer', '-')}\n"
        f"Направление: {data.get('direction', '-')}\n"
        f"Вылет: {data.get('departure', '-')}\n"
        f"Тип дрона: {data.get('drone_type', '-')}\n"
        f"Управление: {data.get('control', '-')}\n"
        f"Видео: {data.get('video_link', '-')}\n"
        f"Спарка: {data.get('sparka', '-')}\n"
        f"Боевая часть: {data.get('warhead', '-')}\n"
        f"Тип взрывателя: {data.get('fuze_type', '-')}\n"
        f"Дальность: {data.get('range_', '-')}\n"
        f"Задача: {data.get('task', '-')}\n"
        f"Результат: {data.get('result', '-')}\n"
        f"Уточнение: {data.get('clarification', '-')}\n"
        f"Координаты: X={data.get('coord_x', '-')} Y={data.get('coord_y', '-')}\n"
        f"Возврат: {data.get('return_', '-')}\n"
        f"Видео: {data.get('video_', '-')}"
    )
    await message.answer(report)
    await message.answer("✅ Отчёт готов! Отправь /otchet для нового.")


async def ask_next_field(message: types.Message, state: FSMContext, current_field: str):
    next_item = get_next_field(current_field)
    if next_item is None:
        await finish_report(message, state)
        return

    next_name, next_label = next_item
    await state.set_state(getattr(ReportForm, next_name))

    saved = SAVED_VALUES.get(next_name, [])

    if saved and next_name not in ("date", "time"):
        kb = make_keyboard(next_name)
        await message.answer(f"{next_label}:", reply_markup=kb)
        return

    if next_name == "date":
        now = datetime.now()
        auto_date = now.strftime("%d.%m.%Y")
        await state.update_data(date=auto_date)
        add_saved_value("date", auto_date)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить дату", callback_data="confirm:date")],
            [InlineKeyboardButton(text="✏️ Изменить дату", callback_data="manual:date")]
        ])
        await message.answer(f"📅 Дата: {auto_date}\nПодтвердить или изменить?", reply_markup=kb)
        return

    if next_name == "time":
        now = datetime.now()
        auto_time = now.strftime("%H:%M")
        await state.update_data(time=auto_time)
        add_saved_value("time", auto_time)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить текущее время", callback_data="confirm:time")],
            [InlineKeyboardButton(text="✏️ Ввести другое время", callback_data="manual:time")]
        ])
        await message.answer(f"⏰ Время: {auto_time}\nПодтвердить текущее или ввести своё?", reply_markup=kb)
        return

    await message.answer(f"{next_label}:")


# --- Callback обработчики ---

@dp.callback_query(F.data.startswith("sel:"))
async def cb_select(callback: types.CallbackQuery, state: FSMContext):
    _, field_name, value = callback.data.split(":", 2)
    await state.update_data(**{field_name: value})
    add_saved_value(field_name, value)
    await callback.message.edit_text(f"{FIELDS_MAP[field_name]}: {value} ✅")
    await ask_next_field(callback.message, state, field_name)
    await callback.answer()


@dp.callback_query(F.data.startswith("manual:"))
async def cb_manual(callback: types.CallbackQuery, state: FSMContext):
    _, field_name = callback.data.split(":", 1)
    await callback.message.edit_text(f"{FIELDS_MAP[field_name]}: введи значение:")
    await callback.answer()


@dp.callback_query(F.data.startswith("confirm:"))
async def cb_confirm(callback: types.CallbackQuery, state: FSMContext):
    _, field_name = callback.data.split(":", 1)
    data = await state.get_data()
    value = data.get(field_name, "")
    add_saved_value(field_name, value)
    await callback.message.edit_text(f"{FIELDS_MAP[field_name]}: {value} ✅")
    await ask_next_field(callback.message, state, field_name)
    await callback.answer()


# --- Команды ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    has_saved = bool(SAVED_VALUES)
    if has_saved:
        await message.answer(
            "Привет! Отправь /otchet для нового отчёта.\n"
            "Для каждого поля будут кнопки с прошлыми значениями — можно выбрать или ввести вручную."
        )
    else:
        await message.answer(
            "Привет! Отправь /otchet для первого отчёта.\n"
            "Заполни все поля вручную — бот запомнит их и в следующий раз предложит кнопками."
        )


@dp.message(Command("otchet"))
async def cmd_otchet(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(ReportForm.date)
    now = datetime.now()
    auto_date = now.strftime("%d.%m.%Y")
    auto_time = now.strftime("%H:%M")

    await state.update_data(date=auto_date, time=auto_time)
    add_saved_value("date", auto_date)
    add_saved_value("time", auto_time)

    kb_date = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить дату", callback_data="confirm:date")],
        [InlineKeyboardButton(text="✏️ Изменить дату", callback_data="manual:date")]
    ])
    await message.answer(f"📋 Заполняем отчёт.\n📅 Дата: {auto_date}", reply_markup=kb_date)


@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Заполнение отменено.")


@dp.message(Command("clear_saved"))
async def cmd_clear_saved(message: types.Message, state: FSMContext):
    global SAVED_VALUES
    SAVED_VALUES = {}
    if os.path.exists(SAVED_FILE):
        os.remove(SAVED_FILE)
    await message.answer("🗑 Все сохранённые варианты очищены.")


# --- Обработчики текстового ввода ---

async def process_text_field(message: types.Message, state: FSMContext, field_name: str):
    text = message.text.strip() if message.text else ""
    if not text:
        await message.answer("Поле не может быть пустым. Введи значение:")
        return
    await state.update_data(**{field_name: text})
    add_saved_value(field_name, text)
    await ask_next_field(message, state, field_name)


@dp.message(ReportForm.date)
async def m_date(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "date")


@dp.message(ReportForm.time)
async def m_time(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "time")


@dp.message(ReportForm.operator)
async def m_operator(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "operator")


@dp.message(ReportForm.engineer)
async def m_engineer(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "engineer")


@dp.message(ReportForm.direction)
async def m_direction(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "direction")


@dp.message(ReportForm.departure)
async def m_departure(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "departure")


@dp.message(ReportForm.drone_type)
async def m_drone_type(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "drone_type")


@dp.message(ReportForm.control)
async def m_control(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "control")


@dp.message(ReportForm.video_link)
async def m_video_link(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "video_link")


@dp.message(ReportForm.sparka)
async def m_sparka(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "sparka")


@dp.message(ReportForm.warhead)
async def m_warhead(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "warhead")


@dp.message(ReportForm.fuze_type)
async def m_fuze_type(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "fuze_type")


@dp.message(ReportForm.range_)
async def m_range(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "range_")


@dp.message(ReportForm.task)
async def m_task(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "task")


@dp.message(ReportForm.result)
async def m_result(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "result")


@dp.message(ReportForm.clarification)
async def m_clarification(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "clarification")


@dp.message(ReportForm.coord_x)
async def m_coord_x(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "coord_x")


@dp.message(ReportForm.coord_y)
async def m_coord_y(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "coord_y")


@dp.message(ReportForm.return_)
async def m_return(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "return_")


@dp.message(ReportForm.video_)
async def m_video(message: types.Message, state: FSMContext):
    await process_text_field(message, state, "video_")


# --- Запуск ---

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот запущен. Сохранённых полей: %d", len(SAVED_VALUES))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
