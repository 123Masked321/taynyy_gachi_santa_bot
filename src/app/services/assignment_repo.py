from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.repos.assignment_repo import AssignmentRepo
from src.app.db.repos.game_repo import GameRepo
from src.app.db.repos.player_repo import PlayerRepo
from src.app.utils.shuffle import shuffle_list


@dataclass(frozen=True)
class DrawResult:
    ok: bool
    reason: str
    delivered: int = 0
    failed: int = 0


@dataclass(frozen=True)
class MyReceiverResult:
    ok: bool
    reason: str
    receiver_name: str | None = None
    receiver_username: str | None = None


class AssignmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def draw_and_notify(self, bot: Bot, game_id: int) -> DrawResult:
        game_repo = GameRepo(self.session)
        player_repo = PlayerRepo(self.session)
        assign_repo = AssignmentRepo(self.session)

        players = await player_repo.list_participants(game_id)
        if len(players) < 3:
            return DrawResult(False, "not_enough")

        pairs = shuffle_list([p.id for p in players])

        await assign_repo.save_assignments(game_id, pairs, replace=True)
        await game_repo.set_game_status(game_id, "drawn")

        by_id = {p.id: p for p in players}

        delivered = 0
        failed = 0
        for giver_id, receiver_id in pairs:
            giver = by_id[giver_id]
            receiver = by_id[receiver_id]
            try:
                await bot.send_message(
                    giver.tg_id,
                    f"Твой получатель: <b>{receiver.name}</b>",
                    parse_mode="HTML",
                )
                delivered += 1
            except Exception:
                failed += 1

        return DrawResult(True, "ok", delivered=delivered, failed=failed)

    async def get_my_receiver(self, game_id: int, tg_id: int) -> MyReceiverResult:
        player_repo = PlayerRepo(self.session)
        assign_repo = AssignmentRepo(self.session)

        me = await player_repo.get_player_by_tg(game_id, tg_id)
        if not me:
            return MyReceiverResult(False, "not_joined")

        receiver = await assign_repo.get_receiver_player(game_id, me.id)
        if not receiver:
            return MyReceiverResult(False, "not_drawn")

        return MyReceiverResult(
            True,
            "ok",
            receiver_name=receiver.name,
            receiver_username=receiver.username or None,
        )
