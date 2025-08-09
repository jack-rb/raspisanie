import asyncio
from fastapi import FastAPI, Depends, HTTPException, Path, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
import hmac
import hashlib
from urllib.parse import parse_qsl
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import hmac as _hmaclib

from .core.database import get_db
from .services.schedule import ScheduleService
from .schemas.schedule import Group, Day, Lesson, Teacher
from .bot.bot import bot, setup_bot
from .core.config import settings
from .services.schedule import AuthHelpers

# Простой логгер
import logging
logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

app = FastAPI(title="Schedule API")

# CORS: разрешаем только Telegram WebApp (можно расширить список)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org", "https://web.telegram.org/", "https://t.me"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- SlowAPI Limiter ---
# Кастомная функция для извлечения user_id из Init Data

def get_user_id_from_init_data(request: Request):
    init_data = None
    try:
        body = request._body if hasattr(request, '_body') else None
        if not body:
            body = request.json()
        if isinstance(body, dict):
            init_data = body.get("initData") or body.get("init_data")
    except Exception:
        pass
    if not init_data:
        init_data = request.headers.get("x-telegram-initdata")
    if init_data:
        data = dict(parse_qsl(init_data, strict_parsing=True))
        return str(data.get("user\_id", "anonymous"))
    return "anonymous"

limiter = Limiter(key_func=get_user_id_from_init_data)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Проверка Init Data (перенесена выше, до использования в Depends) ---
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

# Если включён публичный доступ, отключим жёсткую проверку
def check_telegram_init_data(init_data: str) -> bool:
    if settings.ALLOW_PUBLIC:
        return True
    if not TELEGRAM_BOT_TOKEN or not init_data:
        return False
    try:
        data = dict(parse_qsl(init_data, strict_parsing=True))
        hash_ = data.pop('hash', None)
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(data.items()))
        secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
        hmac_string = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        ok = _hmaclib.compare_digest(hmac_string, hash_) if hash_ else False
        if not ok:
            logger.warning("InitData HMAC mismatch")
        return ok
    except Exception as e:
        logger.warning(f"InitData parse error: {e}")
        return False

async def verify_init_data(request: Request, x_telegram_initdata: str = Header(None)):
    if settings.ALLOW_PUBLIC:
        return True
    init_data = None
    try:
        body = await request.json()
        init_data = body.get("initData") or body.get("init_data")
    except Exception:
        pass  # body может отсутствовать для GET
    if not init_data:
        # custom header by our frontend
        init_data = x_telegram_initdata
    if not init_data:
        # official Telegram header
        init_data = request.headers.get("telegram-init-data")
    if not init_data:
        # alternate header name (fallback)
        init_data = request.headers.get("x-init-data") or request.headers.get("x-telegram-web-app-data")
    if not init_data:
        # query param fallback used by some clients
        init_data = request.query_params.get("tgWebAppData") or request.query_params.get("init_data")
    if not init_data or not check_telegram_init_data(init_data):
        logger.info("Auth failed for request %s %s", request.method, request.url.path)
        raise HTTPException(status_code=401, detail="Invalid Telegram Init Data")
    return True
# --- Конец блока проверки Init Data ---

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/test_db")
@limiter.limit("5/second;100/hour")
async def test_db(request: Request, db: Session = Depends(get_db)):
    groups = ScheduleService.get_all_groups(db)
    return {"groups_count": len(groups), "groups": groups}

@app.get("/groups/", response_model=List[Group])
@limiter.limit("5/second;100/hour")
async def get_groups(
    request: Request,
    verified: bool = Depends(verify_init_data),
    db: Session = Depends(get_db)
):
    groups = ScheduleService.get_all_groups(db)
    print("Получены группы из БД:", groups)  # Отладка
    return groups

@app.get("/groups/{group_id}/schedule/{date}", response_model=Day)
@limiter.limit("5/second;100/hour")
async def get_schedule(
    request: Request,
    group_id: int,
    date: str,
    verified: bool = Depends(verify_init_data),
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

@app.get("/teachers/", response_model=List[Teacher])
async def get_teachers(db: Session = Depends(get_db)):
    teachers = ScheduleService.get_all_teachers(db)
    return teachers

@app.get("/teachers/{teacher_name}/schedule/{date}")
@limiter.limit("5/second;100/hour")
async def get_teacher_schedule(
    request: Request,
    teacher_name: str = Path(..., description="ФИО преподавателя"),
    date: str = Path(..., description="Дата в формате YYYY-MM-DD"),
    verified: bool = Depends(verify_init_data),
    db: Session = Depends(get_db)
):
    schedule = ScheduleService.get_teacher_schedule_by_date(db, teacher_name, date)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

# Пример защищённого эндпоинта
@app.post("/secure-endpoint")
@limiter.limit("5/second;100/hour")
async def secure_endpoint(
    request: Request,
    verified: bool = Depends(verify_init_data),
    db: Session = Depends(get_db)
):
    # Ваш код для защищённого эндпоинта
    return {"status": "ok"}

@app.get("/whoami")
async def whoami(request: Request, db: Session = Depends(get_db)):
    # возвращает данные пользователя из initData (без сохранения)
    init_data = request.headers.get("x-telegram-initdata")
    payload = AuthHelpers.verify_init_data(init_data)
    if not payload:
        if settings.ALLOW_PUBLIC:
            return {"user_id": "public"}
        raise HTTPException(status_code=401, detail="Invalid Telegram Init Data")
    return payload

@app.get("/user/selection")
async def get_user_selection(request: Request, db: Session = Depends(get_db)):
    init_data = request.headers.get("x-telegram-initdata")
    payload = AuthHelpers.verify_init_data(init_data)
    if not payload:
        if settings.ALLOW_PUBLIC:
            return {"last_selected_group_id": None, "last_selected_teacher": None}
        raise HTTPException(status_code=401, detail="Invalid Telegram Init Data")
    AuthHelpers.upsert_user(db, payload)
    from .models.schedule import User
    user = db.query(User).filter(User.tg_user_id == payload.get('user_id')).first()
    if not user:
        return {"last_selected_group_id": None, "last_selected_teacher": None}
    return {
        "last_selected_group_id": user.last_selected_group_id,
        "last_selected_teacher": user.last_selected_teacher,
    }

@app.post("/user/selection")
async def set_user_selection(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    init_data = body.get("initData") or request.headers.get("x-telegram-initdata")
    payload = AuthHelpers.verify_init_data(init_data)
    if not payload:
        if not settings.ALLOW_PUBLIC:
            raise HTTPException(status_code=401, detail="Invalid Telegram Init Data")
        # В публичном режиме сохранять нечего
        return {"ok": True}
    AuthHelpers.upsert_user(db, payload)
    AuthHelpers.save_last_selection(
        db,
        user_id=payload.get('user_id'),
        group_id=body.get('group_id'),
        teacher=body.get('teacher'),
    )
    return {"ok": True}

# Запуск бота при старте приложения
@app.on_event("startup")
async def startup_event():
    # Запускаем бота в отдельном потоке через executor, чтобы /start работал
    import threading
    from .bot.bot import run_bot
    threading.Thread(target=run_bot, daemon=True).start()

# Закрытие сессии бота при остановке приложения
@app.on_event("shutdown")
async def shutdown_event():
    try:
        await bot.session.close()
    except Exception:
        pass 