import asyncio

from aiogram import Bot, Dispatcher

from config import settings
from db.database import init_db
from handlers import menu, meal, profile, recipe, reports
from services.limits import RateLimiter


async def main() -> None:
    init_db()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    dp.message.middleware(RateLimiter(rate_limit=2.0))
    dp.callback_query.middleware(RateLimiter(rate_limit=1.0))

    dp.include_router(menu.router)
    dp.include_router(profile.router)
    dp.include_router(recipe.router)
    dp.include_router(reports.router)
    dp.include_router(meal.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())