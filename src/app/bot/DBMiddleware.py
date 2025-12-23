from typing import Callable, Awaitable, Dict, Any
from aiogram import BaseMiddleware
from src.app.db.session import AsyncSessionLocal


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        async with AsyncSessionLocal() as session:  # <- создаём сессию на один апдейт
            data["session"] = session           # <- ключ должен называться как аргумент хендлера
            return await handler(event, data)
