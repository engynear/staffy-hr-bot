import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.enums.parse_mode import ParseMode

from handlers import router
from db import Database, get_db

from sheduler import friday_thank_you, friday_thank_you_prepare, monday_thank_you_prepare

from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler()

def load_config():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    config = {}
    config['BOT_TOKEN'] = os.environ.get('BOT_TOKEN')
    return config

config = load_config()
bot = Bot(token=config['BOT_TOKEN'], parse_mode=ParseMode.HTML)

async def main():
    db = await get_db()
    # await db.drop_tables()
    # print('tables dropped')
    await db.create_tables()
    # await db.add_team('VOVA family', 'The best team in the world')

    storage = RedisStorage.from_url(os.environ.get('REDIS_URL'))
    dp = Dispatcher(storage=MemoryStorage(), bot=bot)

    dp.include_router(router)
    scheduler.add_job(monday_thank_you_prepare, 'cron', day_of_week='mon', hour=11, minute=00, args=[bot])
    scheduler.add_job(friday_thank_you_prepare, 'cron', day_of_week='fri', hour=11, minute=00, args=[bot])
    # scheduler.add_job(friday_thank_you, 'cron', day_of_week='mon', hour=2, minute=51, args=[bot])
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), skip_updates=True)


if __name__ == "__main__":
    logging.basicConfig(filename='bot.log', level=logging.DEBUG)
    asyncio.run(main())