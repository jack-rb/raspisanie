# PSUTI Schedule Bot

Telegram Mini App для просмотра расписания ПГУТИ с возможностью поиска по группам и преподавателям.

## 🚀 Возможности

- 📅 Просмотр расписания по группам
- 👨‍🏫 Просмотр расписания по преподавателям
- 🔗 Кликабельные ссылки для переключения между режимами
- 📱 Адаптивный дизайн для мобильных устройств
- 🔒 Безопасность Telegram WebApp
- ⏰ Отображение текущего времени (Самара)

## 🛠 Технологии

- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Frontend:** HTML5, CSS3, JavaScript, Telegram WebApp API
- **Bot:** aiogram
- **DevOps:** Docker, Docker Compose, Nginx
- **Security:** Telegram WebApp validation, CORS, CSP

## 📦 Установка и запуск

### Локальная разработка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/jack-rb/psuti-schedule-bot.git
cd psuti-schedule-bot
```

2. **Создайте .env файл:**
```bash
DATABASE_URL=sqlite:///./data/schedule.db
BOT_TOKEN=your_bot_token_here
DOMAIN=localhost
SUBDOMAIN_ENABLED=false
```

3. **Запустите через Docker:**
```bash
docker-compose up --build
```

4. **Откройте в браузере:**
```
http://localhost:8000
```

### Продакшен деплой

1. **Загрузите код на сервер:**
```bash
git clone https://github.com/jack-rb/psuti-schedule-bot.git
cd psuti-schedule-bot
```

2. **Создайте .env файл на сервере:**
```bash
DATABASE_URL=sqlite:///./data/schedule.db
BOT_TOKEN=your_production_bot_token
DOMAIN=psuti.raspisanie.space
SUBDOMAIN_ENABLED=true
```

3. **Запустите:**
```bash
docker-compose up -d
```

## 🔧 Конфигурация

### Переменные окружения

- `DATABASE_URL` - URL базы данных
- `BOT_TOKEN` - Токен Telegram бота
- `DOMAIN` - Домен приложения
- `SUBDOMAIN_ENABLED` - Включить поддомен

### DNS настройка

Добавьте A запись:
- Имя: `psuti`
- Значение: IP вашего сервера
- TTL: 300

## 🔒 Безопасность

- ✅ Валидация подписи Telegram WebApp
- ✅ CORS ограничения (только Telegram домены)
- ✅ Content Security Policy
- ✅ Проверка User-Agent и Referer
- ✅ HTTPS с современными шифрами

## 📁 Структура проекта

```
psuti-schedule-bot/
├── app/                    # Основное приложение
│   ├── bot/               # Telegram бот
│   ├── core/              # Конфигурация и БД
│   ├── models/            # Модели SQLAlchemy
│   ├── schemas/           # Pydantic схемы
│   └── services/          # Бизнес-логика
├── static/                # Статические файлы
├── alembic/               # Миграции БД
├── docker-compose.yml     # Docker конфигурация
```

## 🤝 Разработка

### Добавление новых функций

1. Создайте ветку для новой функции
2. Внесите изменения
3. Протестируйте локально
4. Создайте Pull Request

### Тестирование

```bash
# Локальное тестирование
docker-compose up --build

# Продакшен тестирование
docker-compose up --build
```

## 📞 Поддержка

При возникновении проблем создайте Issue в репозитории.

## 📄 Лицензия

MIT License 