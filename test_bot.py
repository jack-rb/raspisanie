from app.bot.bot import bot, dp
import asyncio

async def test_bot():
    try:
        print("Бот запущен")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_bot()) 