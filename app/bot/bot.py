from aiogram import Bot, Dispatcher
from ..core.config import settings

# Инициализация бота
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(bot)  # Для старой версии aiogram нужно передавать bot


def setup_bot():
    # Импортируем обработчики
    from . import handlers  # noqa: F401
    return dp

# Запуск polling через executor (блокирующий) — вызывать в отдельном потоке
from aiogram.utils import executor

def run_bot():
    setup_bot()
    executor.start_polling(dp, skip_updates=True)
