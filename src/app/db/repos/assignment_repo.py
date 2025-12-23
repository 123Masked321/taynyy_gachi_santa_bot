from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.models import Player, Assignment


class AssignmentRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_assignments(
        self,
        game_id: int,
        pairs: Sequence[tuple[int, int]],
        *,
        replace: bool = True,
    ) -> None:
        if replace:
            await self.session.execute(delete(Assignment).where(Assignment.game_id == game_id))

        self.session.add_all(
            [
                Assignment(game_id=game_id, giver_id=giver_id, receiver_id=receiver_id)
                for giver_id, receiver_id in pairs
            ]
        )

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise

    async def get_assignment_for_user(self, game_id: int, giver_id: int) -> Assignment | None:
        res = await self.session.execute(
            select(Assignment).where(
                Assignment.game_id == game_id,
                Assignment.giver_id == giver_id,
            )
        )
        return res.scalar_one_or_none()

    async def get_receiver_player(self, game_id: int, giver_player_id: int) -> Player | None:
        stmt = (
            select(Player)
            .join(Assignment, Assignment.receiver_id == Player.id)
            .where(Assignment.game_id == game_id, Assignment.giver_id == giver_player_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
