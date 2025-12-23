from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.bot.keyboards import role_keyboard, games_list_keyboard, game_keyboard
from src.app.bot.messages import game_created_text, game_info_text, participants_text
from src.app.db.models import Game
from src.app.services.assignment_service import AssignmentService
from src.app.services.game_service import GameService
from src.app.services.player_service import PlayerService
from src.app.utils.link import generate_link

game_router = Router()


class NewGame(StatesGroup):
    processing_name = State()
    processing_money = State()


class CheckGame(StatesGroup):
    processing_role = State()
    processing_group = State()


@game_router.message(Command("create"))
async def enter_name_game(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer('Введи имя игры, leatherman:')
    await state.set_state(NewGame.processing_name)


@game_router.message(F.text, StateFilter(NewGame.processing_name))
async def enter_money_game(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await message.answer('Приблизительная цена подарков для гоев:')
    await state.set_state(NewGame.processing_money)


@game_router.message(F.text, StateFilter(NewGame.processing_money))
async def create_new_game(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    name: str = data['name']
    money: str = message.text.strip()

    game_serv = GameService(session)
    game: Game = await game_serv.create_game(name, money, message.from_user.id)
    link: str = generate_link(game.code)
    await state.clear()

    await message.answer(text=game_created_text(game.code, link))


@game_router.message(Command("groups"))
async def check_groups(message: Message, state: FSMContext) -> None:
    await message.answer("Выбери роль для групп, где ты хочешь чекнуть", reply_markup=role_keyboard())
    await state.set_state(CheckGame.processing_role)


@game_router.callback_query(F.data.startswith("role_"), StateFilter(CheckGame.processing_role))
async def check_role(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    role: str = callback.data.split("_")[1].strip()
    await state.update_data(role=role)

    game_serv = GameService(session)
    games = await game_serv.get_games_by_role(callback.from_user.id, role)

    if not games:
        await callback.message.edit_text(
            "Не нашёл игр по выбранной роли 😕"
        )
        return

    await callback.message.edit_text(
        "Выбери игру:",
        reply_markup=games_list_keyboard(games)
    )
    await state.set_state(CheckGame.processing_group)


async def render_game_screen(
    callback: CallbackQuery,
    session: AsyncSession,
    *,
    game_id: int,
    is_admin: bool,
) -> None:
    game_serv = GameService(session)

    dto = await game_serv.get_game_info_by_id(game_id)

    if not dto:
        await callback.answer("Игра не найдена", show_alert=True)
        return

    await callback.message.edit_text(
        game_info_text(dto),
        reply_markup=game_keyboard(dto.id, is_admin, dto.status),
        disable_web_page_preview=True,
    )


@game_router.callback_query(F.data.startswith("game_"), StateFilter(CheckGame.processing_group))
async def check_game(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    game_id = int(callback.data.split("_", 1)[1].strip())

    data = await state.get_data()
    is_admin = (data.get("role") == "owner")  # или "admin" — как у тебя принято

    await render_game_screen(callback, session, game_id=game_id, is_admin=is_admin)
    await state.clear()


@game_router.callback_query(F.data.startswith("lock_"))
async def check_game_lock(callback: CallbackQuery, session: AsyncSession) -> None:
    game_id: int = int(callback.data.split("_")[1].strip())
    game_serv = GameService(session)
    await game_serv.lock_game(game_id)
    await render_game_screen(callback, session, game_id=game_id, is_admin=True)


@game_router.callback_query(F.data.startswith("unlock_"))
async def check_game_unlock(callback: CallbackQuery, session: AsyncSession) -> None:
    game_id: int = int(callback.data.split("_")[1].strip())
    game_serv = GameService(session)
    await game_serv.open_game(game_id)
    await render_game_screen(callback, session, game_id=game_id, is_admin=True)


@game_router.callback_query(F.data.startswith("leave_"))
async def leave_cb(callback: CallbackQuery, session: AsyncSession) -> None:
    game_id = int(callback.data.split("_", 1)[1].strip())

    player_serv = PlayerService(session)
    ok = await player_serv.leave_game(game_id, callback.from_user.id)

    if not ok:
        await callback.answer("Не получилось выйти", show_alert=True)
        return

    await callback.message.answer("Ты вышел из группы ✅")


@game_router.callback_query(F.data.startswith("drop_"))
async def drop_cb(callback: CallbackQuery, session: AsyncSession) -> None:
    game_id = int(callback.data.split("_", 1)[1].strip())

    serv = GameService(session)
    ok = await serv.drop_game(game_id)

    if not ok:
        await callback.answer("Игра не найдена", show_alert=True)
        return

    await callback.message.answer("Группа удалена 🗑️")


@game_router.callback_query(F.data.startswith("plist_"))
async def plist_cb(callback: CallbackQuery, session: AsyncSession) -> None:
    game_id = int(callback.data.split("_", 1)[1].strip())

    player_serv = PlayerService(session)
    players = await player_serv.get_list_participants(game_id)

    await callback.message.answer(participants_text(players))
    await callback.answer()


@game_router.callback_query(F.data.startswith("draw_"))
async def draw_cb(callback: CallbackQuery, session: AsyncSession) -> None:
    game_id = int(callback.data.split("_", 1)[1].strip())

    serv = AssignmentService(session)
    res = await serv.draw_and_notify(callback.bot, game_id)

    if not res.ok:
        if res.reason == "not_enough":
            await callback.answer("Нужно минимум 3 участника", show_alert=True)
        else:
            await callback.answer("Не получилось разыграть", show_alert=True)
        return

    await callback.message.answer("Распределение сделано 🎲")
    await callback.message.answer(f"🎲 Готово! В личку доставлено: ✅ {res.delivered}, ❌ {res.failed}")


@game_router.callback_query(F.data.startswith("my_"))
async def my_cb(callback: CallbackQuery, session: AsyncSession) -> None:
    game_id = int(callback.data.split("_", 1)[1].strip())

    serv = AssignmentService(session)
    res = await serv.get_my_receiver(game_id, callback.from_user.id)

    if not res.ok:
        if res.reason == "not_joined":
            await callback.message.answer("Ты не участник этой игры", show_alert=True)
        else:
            await callback.message.answer("Подарки ещё не распределены 🎲", show_alert=True)
        return

    uname = f" (@{res.receiver_username})" if res.receiver_username else ""
    await callback.message.answer(f"Твой получатель: <b>{res.receiver_name}</b>{uname}", parse_mode="HTML")



