import asyncio
from fastapi import FastAPI, Depends, HTTPException, Path, Header, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
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
from fastapi.middleware.cors import CORSMiddleware

from .core.database import get_db
from .services.schedule import ScheduleService
from .schemas.schedule import Group, Day, Lesson, Teacher
from .bot.bot import bot, setup_bot
from .core.config import settings
from .services.schedule import AuthHelpers

from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from uuid import uuid4

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
    try:
        # Читаем из заголовков (без попытки читать тело у async запроса)
        for h in ("telegram-init-data", "x-telegram-web-app-data", "x-init-data", "x-telegram-initdata"):
            v = request.headers.get(h)
            if not v:
                continue
            try:
                from urllib.parse import parse_qsl
                import json
                data = dict(parse_qsl(v, keep_blank_values=True, strict_parsing=False, encoding='utf-8', errors='ignore'))
                if 'user' in data:
                    u = json.loads(data['user'])
                    uid = u.get('id')
                    if uid is not None:
                        return str(uid)
            except Exception:
                continue
    except Exception:
        pass
    # Фоллбек: IP-адрес
    try:
        from slowapi.util import get_remote_address
        return get_remote_address(request) or "anonymous"
    except Exception:
        return "anonymous"

limiter = Limiter(key_func=get_user_id_from_init_data)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Проверка Init Data (перенесена выше, до использования в Depends) ---
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
if TELEGRAM_BOT_TOKEN:
    TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN.strip()

# Если включён публичный доступ, отключим жёсткую проверку
def _extract_init_data(request: Request, x_telegram_initdata: str | None) -> tuple[str | None, str]:
    # 1) body (POST)
    init_data = None
    try:
        # тело уже будет прочитано в verify, здесь только fallback
        pass
    except Exception:
        pass
    if init_data:
        return init_data, "body.initData"

    # 2) официальные/альтернативные заголовки (ПРИОРИТЕТ)
    for h in ("telegram-init-data", "x-telegram-web-app-data", "x-init-data"):
        v = request.headers.get(h)
        if v:
            return v, f"hdr.{h}"

    # 3) наш заголовок (Fallback)
    if x_telegram_initdata:
        return x_telegram_initdata, "hdr.X-Telegram-InitData"

    # 4) query
    for q in ("tgWebAppData", "init_data"):
        v = request.query_params.get(q)
        if v:
            return v, f"qry.{q}"

    return None, "none"


def check_telegram_init_data(init_data: str, src: str) -> bool:
    if settings.ALLOW_PUBLIC:
        return True
    if not TELEGRAM_BOT_TOKEN or not init_data:
        logger.warning("InitData empty or no BOT_TOKEN (src=%s)", src)
        return False
    try:
        # Normalize init_data
        init_data = init_data.strip()
        if len(init_data) >= 2 and ((init_data[0] == '"' and init_data[-1] == '"') or (init_data[0] == "'" and init_data[-1] == "'")):
            init_data = init_data[1:-1]
        data = dict(parse_qsl(
            init_data,
            keep_blank_values=True,
            strict_parsing=False,
            encoding='utf-8',
            errors='ignore'
        ))
        recv_hash = data.pop('hash', None) or ""
        # Формируем строку проверки ИЗ ВСЕХ полученных полей (кроме hash), как в доках Telegram
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(data.items()))
        secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
        local_hmac = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        ok = _hmaclib.compare_digest(local_hmac, recv_hash)
        if not ok:
            logger.warning(
                "InitData HMAC mismatch (src=%s, len=%s, recv=%s..., calc=%s...)",
                src, len(init_data), recv_hash[:8], local_hmac[:8]
            )
        return ok
    except Exception as e:
        logger.warning("InitData parse error (src=%s): %s", src, e)
        return False

async def verify_init_data(request: Request, x_telegram_initdata: str = Header(None)):
    if settings.ALLOW_PUBLIC:
        return True
    # 1) читаем тело для POST
    init_data_body = None
    try:
        body = await request.json()
        if isinstance(body, dict):
            init_data_body = body.get("initData") or body.get("init_data")
    except Exception:
        pass

    if init_data_body:
        init_data, src = init_data_body, "body.initData"
    else:
        init_data, src = _extract_init_data(request, x_telegram_initdata)

    if not init_data or not check_telegram_init_data(init_data, src):
        logger.info("Auth failed %s %s (src=%s)", request.method, request.url.path, src)
        raise HTTPException(status_code=401, detail="Invalid Telegram Init Data")
    return True
# --- Конец блока проверки Init Data ---

def _is_telegram_webview(request: Request) -> bool:
    ua = (request.headers.get("user-agent") or "").lower()
    return any(marker in ua for marker in ("telegram", "webview", "tgwebview", "telegramwebview"))

def _extract_user_from_init_data(init_data: str) -> dict | None:
    try:
        import json
        data = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False, encoding='utf-8', errors='ignore'))
        if 'user' in data:
            u = json.loads(data['user'])
            return {
                "user_id": int(u.get('id')) if u.get('id') is not None else None,
                "username": u.get('username'),
                "first_name": u.get('first_name'),
                "last_name": u.get('last_name'),
                "language_code": u.get('language_code')
            }
        if 'user_id' in data:
            return {"user_id": int(data['user_id'])}
    except Exception:
        pass
    return None

async def verify_telegram_mini_app(request: Request, x_telegram_initdata: str = Header(None)):
    # Разрешение на публичный доступ только как временный костыль (отключить в проде)
    if settings.ALLOW_PUBLIC:
        return {"user_id": "public"}

    # Доступ только из Telegram WebView
    if not _is_telegram_webview(request):
        bot_username = settings.BOT_USERNAME or ""
        if bot_username:
            raise HTTPException(status_code=302, detail="open in Telegram", headers={"Location": f"https://t.me/{bot_username}"})
        raise HTTPException(status_code=403, detail="Access denied: open via Telegram")

    # Ищем initData: тело -> заголовки -> query
    init_data_body = None
    try:
        if request.method == "POST":
            body = await request.json()
            if isinstance(body, dict):
                init_data_body = body.get("initData") or body.get("init_data")
    except Exception:
        pass
    if init_data_body:
        init_data, src = init_data_body, "body.initData"
    else:
        init_data, src = _extract_init_data(request, x_telegram_initdata)

    if not init_data or not check_telegram_init_data(init_data, src):
        logger.info("Auth failed %s %s (src=%s)", request.method, request.url.path, src)
        raise HTTPException(status_code=401, detail="Invalid Telegram Init Data")

    user = _extract_user_from_init_data(init_data)
    if not user or not user.get("user_id"):
        raise HTTPException(status_code=401, detail="Invalid user in Init Data")
    return user

@app.get("/")
async def root(request: Request):
    """Главная страница расписания ПГУТИ (только через Telegram WebView)"""
    if not _is_telegram_webview(request):
        bot_username = settings.BOT_USERNAME or ""
        if bot_username:
            return RedirectResponse(url=f"https://t.me/{bot_username}", status_code=302)
        raise HTTPException(status_code=403, detail="Access denied: open via Telegram")
    return FileResponse("static/index.html")

@app.get("/calendar.html")
async def calendar(request: Request):
    """Страница календаря расписания ПГУТИ (только через Telegram WebView)"""
    if not _is_telegram_webview(request):
        bot_username = settings.BOT_USERNAME or ""
        if bot_username:
            return RedirectResponse(url=f"https://t.me/{bot_username}", status_code=302)
        raise HTTPException(status_code=403, detail="Access denied: open via Telegram")
    return FileResponse("static/calendar.html")

@app.get("/sitemap.xml")
async def sitemap():
    """Sitemap для поисковых систем"""
    sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://raspisanie.space/</loc>
        <lastmod>2025-08-09</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://raspisanie.space/calendar.html</loc>
        <lastmod>2025-08-09</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>"""
    return Response(content=sitemap_content, media_type="application/xml")

@app.get("/robots.txt")
async def robots():
    """Robots.txt для поисковых систем"""
    robots_content = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/

Sitemap: https://raspisanie.space/sitemap.xml"""
    return Response(content=robots_content, media_type="text/plain")

@app.get("/test_db")
@limiter.limit("5/second;100/hour")
async def test_db(request: Request, user: dict = Depends(verify_telegram_mini_app), db: Session = Depends(get_db)):
    groups = ScheduleService.get_all_groups(db)
    return {"groups_count": len(groups), "groups": groups, "user": user}

@app.get("/groups/", response_model=List[Group])
@limiter.limit("5/second;100/hour")
async def get_groups(
    request: Request,
    user: dict = Depends(verify_telegram_mini_app),
    db: Session = Depends(get_db)
):
    groups = ScheduleService.get_all_groups(db)
    return groups

@app.get("/groups/{group_id}/schedule/{date}", response_model=Day)
@limiter.limit("5/second;100/hour")
async def get_schedule(
    request: Request,
    group_id: int,
    date: str,
    user: dict = Depends(verify_telegram_mini_app),
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
async def get_lessons(
    day_id: int,
    user: dict = Depends(verify_telegram_mini_app),
    db: Session = Depends(get_db)
):
    return ScheduleService.get_lessons_by_day_id(db, day_id)

@app.get("/teachers/", response_model=List[Teacher])
async def get_teachers(
    user: dict = Depends(verify_telegram_mini_app),
    db: Session = Depends(get_db)
):
    teachers = ScheduleService.get_all_teachers(db)
    return teachers

@app.get("/teachers/{teacher_name}/schedule/{date}")
@limiter.limit("5/second;100/hour")
async def get_teacher_schedule(
    request: Request,
    teacher_name: str = Path(..., description="ФИО преподавателя"),
    date: str = Path(..., description="Дата в формате YYYY-MM-DD"),
    user: dict = Depends(verify_telegram_mini_app),
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
    user: dict = Depends(verify_telegram_mini_app),
    db: Session = Depends(get_db)
):
    # Ваш код для защищённого эндпоинта
    return {"status": "ok"}

@app.get("/whoami")
async def whoami(user: dict = Depends(verify_telegram_mini_app)):
    return {
        "user_id": user.get("user_id"),
        "username": user.get("username"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "source": "telegram_mini_app"
    }

@app.get("/user/selection")
async def get_user_selection(user: dict = Depends(verify_telegram_mini_app), db: Session = Depends(get_db)):
    if user.get('user_id') == "public":
        return {"last_selected_group_id": None, "last_selected_teacher": None}
    AuthHelpers.upsert_user(db, user)
    from .models.schedule import User
    u = db.query(User).filter(User.tg_user_id == user.get('user_id')).first()
    if not u:
        return {"last_selected_group_id": None, "last_selected_teacher": None}
    return {
        "last_selected_group_id": u.last_selected_group_id,
        "last_selected_teacher": u.last_selected_teacher,
    }

@app.post("/user/selection")
async def set_user_selection(request: Request, user: dict = Depends(verify_telegram_mini_app), db: Session = Depends(get_db)):
    body = await request.json()
    if user.get('user_id') == "public":
        return {"ok": True}
    AuthHelpers.upsert_user(db, user)
    AuthHelpers.save_last_selection(
        db,
        user_id=user.get('user_id'),
        group_id=body.get('group_id'),
        teacher=body.get('teacher'),
    )
    return {"ok": True}

@app.get("/config-public")
async def config_public():
    return {
        "bot_username": settings.BOT_USERNAME,
        "domain": settings.DOMAIN
    }

@app.post("/webapp/submit")
@limiter.limit("5/second;100/hour")
async def webapp_submit(request: Request, user: dict = Depends(verify_telegram_mini_app)):
    body = await request.json()
    query_id = body.get("query_id")
    if not query_id:
        raise HTTPException(status_code=400, detail="query_id required")
    # Build result
    payload = body.get("data")
    text = f"Данные получены: {payload}" if payload is not None else "Данные получены"
    result = InlineQueryResultArticle(
        id=str(uuid4()),
        title="Отправлено",
        input_message_content=InputTextMessageContent(text)
    )
    try:
        await bot.answer_web_app_query(query_id, result)
    except Exception as e:
        logger.warning(f"answer_web_app_query error: {e}")
        raise HTTPException(status_code=500, detail="Failed to answer web app query")
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