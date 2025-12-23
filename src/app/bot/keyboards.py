from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.app.db.models import Game


def game_keyboard(game_id: int, is_admin: bool, status: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="Список участников", callback_data=f"plist_{game_id}")
    kb.button(text="Мой получатель", callback_data=f"my_{game_id}")

    if is_admin:
        is_open = (status == "open")
        is_drawn = (status == "drawn")
        if is_open:
            kb.button(text="🔒 Закрыть группу", callback_data=f"lock_{game_id}")
        else:
            kb.button(text="🔓 Открыть группу", callback_data=f"unlock_{game_id}")
        kb.button(text="🎲 Распределить подарки", callback_data=f"draw_{game_id}")
        kb.button(text="Удалить группу", callback_data=f"drop_{game_id}")
    else:
        kb.button(text="Покинуть группу", callback_data=f"leave_{game_id}")

    kb.adjust(1, 1, 2 if is_admin else 1)
    return kb.as_markup()


def role_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Админ", callback_data=f"role_owner")
    kb.button(text="Участник", callback_data=f"role_player")
    kb.adjust(1)
    return kb.as_markup()


def games_list_keyboard(games: list[Game]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for game in games:
        kb.button(text=f"🎁 {game.name}", callback_data=f"game_{game.id}")
    kb.adjust(1)
    return kb.as_markup()
