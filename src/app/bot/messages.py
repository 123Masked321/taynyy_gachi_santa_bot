from __future__ import annotations

from typing import Iterable

from src.app.db.models import Game, Player
from src.app.services.game_service import GameInfoDTO


def welcome_text() -> str:
    return (
        "<b>Тайный Гачи Санта</b>\n\n"
        "Здарова, гои. Да будет лудка!\n"
        "Сейчас узнаем кто кого будет прогревать\n"
    )


def game_created_text(code: str, deep_link: str) -> str:
    return (
        f"Игра создана!\n\n"
        f"Код: <code>{code}</code>\n"
        f"Lube для входа: {deep_link}\n\n"
    )


def game_info_text(dto: GameInfoDTO) -> str:
    drawn = dto.status in {"shuffled"}  # подстрой под свои статусы
    status_line = "🎲 fisting проведено" if drawn else "⏳ fisting не проведено"

    return (
        f"<b>{dto.name}</b>\n"
        f"Код: <code>{dto.code}</code>\n"
        f"Статус: {status_line} ({dto.status})\n"
        f"Гачистов: <b>{dto.participants}</b>\n"
        f"Цена подарков: <b>{dto.money}</b>\n"
        f"Lube: {dto.deep_link}"
    )


def participants_text(players: list[Player]) -> str:
    if not players:
        return "Участников пока нет."

    lines = ["<b>Участники:</b>"]
    for i, p in enumerate(players, start=1):
        uname = f"@{p.username}" if p.username else ""
        lines.append(f"{i}. {p.name} {uname}".strip())
    return "\n".join(lines)
