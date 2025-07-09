import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from .core.database import get_db
from .services.schedule import ScheduleService
from .schemas.schedule import Group, Day, Lesson
from .bot.bot import bot, setup_bot

app = FastAPI(title="Schedule API")

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/test_db")
async def test_db(db: Session = Depends(get_db)):
    groups = ScheduleService.get_all_groups(db)
    return {"groups_count": len(groups), "groups": groups}

@app.get("/groups/", response_model=List[Group])
async def get_groups(db: Session = Depends(get_db)):
    groups = ScheduleService.get_all_groups(db)
    print("Получены группы из БД:", groups)  # Отладка
    return groups

@app.get("/groups/{group_id}/schedule/{date}", response_model=Day)
async def get_schedule(
    group_id: int,
    date: str,
    db: Session = Depends(get_db)
):
    print(f"Запрос расписания для группы {group_id} на дату {date}")  # Отладка
    schedule = ScheduleService.get_schedule_by_date(db, group_id, date)
    if not schedule:
        print(f"Расписание не найдено")  # Отладка
        raise HTTPException(status_code=404, detail="Schedule not found")
    print(f"Найдено расписание: {schedule}")  # Отладка
    return schedule

@app.get("/days/{day_id}/lessons", response_model=List[Lesson])
async def get_lessons(day_id: int, db: Session = Depends(get_db)):
    return ScheduleService.get_lessons_by_day_id(db, day_id)

# Запуск бота при старте приложения
@app.on_event("startup")
async def startup_event():
    # Запуск бота
    dp = setup_bot()
    asyncio.create_task(dp.start_polling(bot))

# Закрытие сессии бота при остановке приложения
@app.on_event("shutdown")
async def shutdown_event():
    await bot.session.close() 