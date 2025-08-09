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
import logging


def run_bot():
    setup_bot()

    async def on_startup(dispatcher):
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logging.getLogger("bot").info("Webhook removed, starting polling")
        except Exception as e:
            logging.getLogger("bot").warning(f"Webhook delete error: {e}")

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
