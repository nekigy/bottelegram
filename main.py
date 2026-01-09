import asyncio
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from config import SHOP_BOT_TOKEN, ADMIN_BOT_TOKEN
from database import init_all
from shop_bot import shop_dp
from admin_bot import admin_dp

init_all()

shop_bot = Bot(SHOP_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
admin_bot = Bot(ADMIN_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

shop_dp.bot = shop_bot
admin_dp.bot = admin_bot

async def main():
    await asyncio.gather(
        shop_dp.start_polling(shop_bot),
        admin_dp.start_polling(admin_bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
