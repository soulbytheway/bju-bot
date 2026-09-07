import time

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


class RateLimiter(BaseMiddleware):
    def __init__(self, rate_limit: float = 2.0):
        self.rate_limit = rate_limit
        self.last_request: dict[int, float] = {}

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")

        if user is not None:
            now = time.monotonic()
            last = self.last_request.get(user.id)

            if last is not None and (now - last) < self.rate_limit:
                if isinstance(event, (CallbackQuery, Message)):
                    await event.answer("Занадто швидко, зачекай секунду")
                return

            self.last_request[user.id] = now

        return await handler(event, data)