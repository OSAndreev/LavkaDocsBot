import asyncio
from aiogram import Bot, Dispatcher
from handlers import common
import time

bot = Bot(token="5867748710:AAFPQXrAQeaRfvUnAtuYKsJmshEyoTo0iW8")


async def main():
    global bot
    dp = Dispatcher()
    dp.include_router(common.router)
    await bot.delete_webhook(drop_pending_updates=True)
    common.scheduler.start()
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
