from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.bot.messages import welcome_text
from src.app.services.player_service import PlayerService

start_router = Router()


class StartRegistration(StatesGroup):
    waiting_name = State()


async def ask_name_for_join(message: Message, state: FSMContext, code: str) -> None:
    await state.clear()
    await state.update_data(join_code=code.strip())

    default_name = (message.from_user.full_name or "Van").strip()
    await message.answer(
        f"Введи как ты будешь подписан:\n"
        f"По умолчанию: {default_name}\n"
    )
    await state.set_state(StartRegistration.waiting_name)


async def precheck_and_ask_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    code: str,
) -> None:
    code = (code or "").strip()
    if not code:
        await message.answer("Используй: /join <CODE>")
        return

    player_serv = PlayerService(session)
    chk = await player_serv.precheck_join_by_code(
        code=code,
        tg_id=message.from_user.id,
        require_collecting=True,
    )

    if chk.reason == "not_found":
        await state.clear()
        await message.answer("Не нашёл игру по этому коду 😕")
        return

    if chk.reason == "closed":
        await state.clear()
        await message.answer(f"В игру «{chk.game.name}» уже нельзя вступить.")
        return

    if chk.reason == "already_joined":
        await state.clear()
        await message.answer(f"Ты уже в игре «{chk.game.name}»\n Информация про группы: /groups")
        return

    await ask_name_for_join(message, state, code)


@start_router.message(CommandStart())
async def start(message: Message, state: FSMContext, command: CommandObject, session: AsyncSession) -> None:
    await message.answer(welcome_text())
    if not command.args:
        await state.clear()
        return

    await precheck_and_ask_name(message, state, session, command.args)


@start_router.message(Command("join"))
async def join_cmd(message: Message, state: FSMContext, command: CommandObject, session: AsyncSession) -> None:
    if not command.args:
        await message.answer("Используй /join CODE")
        return

    await precheck_and_ask_name(message, state, session, command.args)


@start_router.message(F.text, StateFilter(StartRegistration.waiting_name))
async def finish_join(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    code: str = (data.get("join_code") or "").strip()

    name_raw = (message.text or "").strip()
    name = (message.from_user.full_name or "Van").strip() if name_raw in {"-", " "} else name_raw
    username = message.from_user.username or ""

    serv = PlayerService(session)
    res = await serv.join_game_by_code(
        code=code,
        tg_id=message.from_user.id,
        name=name,
        username=username
    )

    await message.answer(f"Ты участвуешь) Жди теперь\n Информация про группы: /groups")
