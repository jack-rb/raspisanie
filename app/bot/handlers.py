from aiogram import types
from aiogram.dispatcher.filters import Command
from datetime import datetime
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.schedule import ScheduleService
from .bot import dp

@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Нажмите на кнопку ниже, чтобы открыть расписание",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text="Открыть расписание",
                web_app=types.WebAppInfo(url="https://raspisanie.space")
            )
        ]])
    )

@dp.message_handler(Command("groups"))
async def cmd_groups(message: types.Message):
    db = next(get_db())
    groups = ScheduleService.get_all_groups(db)
    groups_text = "\n".join([f"• Группа {g.name} (ID: {g.id})" for g in groups])
    await message.answer(
        "Доступные группы:\n\n"
        f"{groups_text}"
    )

@dp.message_handler(Command("schedule"))
async def cmd_schedule(message: types.Message):
    try:
        cmd_parts = message.text.split()
        if len(cmd_parts) != 2:
            await message.answer(
                "Пожалуйста, укажите ID группы.\n"
                "Пример: /schedule 1"
            )
            return
        
        group_id = int(cmd_parts[1])
        today = datetime.now().strftime("%Y-%m-%d")
        
        db = next(get_db())
        schedule = ScheduleService.get_schedule_by_date(db, group_id, today)
        if not schedule:
            await message.answer(f"Расписание на {today} не найдено")
            return
            
        lessons = schedule.get('lessons', [])
        if not lessons:
            await message.answer("На этот день пар нет")
            return
            
        lessons_text = "\n\n".join([
            f"🕒 {lesson['time']}\n"
            f"📚 {lesson['subject']}\n"
            f"👨‍🏫 {lesson['teacher']}\n"
            f"🏛 {lesson['classroom']}"
            for lesson in lessons
        ])
            
        await message.answer(
            f"Расписание на {today}:\n\n"
            f"{lessons_text}"
        )
            
    except ValueError:
        await message.answer("ID группы должен быть числом")
    except Exception as e:
        await message.answer("Произошла ошибка при получении расписания")
