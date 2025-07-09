from aiogram import Bot, Dispatcher
from ..core.config import settings

# Инициализация бота
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(bot)  # Для старой версии aiogram нужно передавать bot

def setup_bot():
    # Импортируем обработчики
    from . import handlers
    return dp
