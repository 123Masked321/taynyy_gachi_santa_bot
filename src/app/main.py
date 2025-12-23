import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.app.bot.DBMiddleware import DbSessionMiddleware
from src.app.settings import settings

from aiogram.types import BotCommand, BotCommandScopeDefault

from src.app.bot.handlers.game import game_router
from src.app.bot.handlers.start import start_router


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="create", description="Создать игру"),
        BotCommand(command="join", description="Вступить в игру"),
        BotCommand(command="groups", description="Посмотреть информацию про все группы"),
        BotCommand(command="start", description="Стартовое сообщение"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def main():
    bot = Bot(token=settings.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML),)
    dp = Dispatcher()

    dp.include_router(game_router)
    dp.include_router(start_router)

    dp.update.middleware(DbSessionMiddleware())

    await set_commands(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
