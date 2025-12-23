from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.models import Player


class PlayerRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_participant(self, game_id: int, tg_id: int, name: str, username: str) -> Player:
        player = Player(game_id=game_id, tg_id=tg_id, name=name, username=username)
        self.session.add(player)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(player)
        return player

    async def list_participants(self, game_id: int) -> list[Player]:
        res = await self.session.execute(
            select(Player).where(Player.game_id == game_id).order_by(Player.id.asc())
        )
        return list(res.scalars().all())

    async def get_player_by_id(self, player_id: int) -> Player | None:
        res = await self.session.execute(select(Player).where(Player.id == player_id))
        return res.scalar_one_or_none()

    async def get_player_by_tg(self, game_id: int, tg_id: int) -> Player | None:
        res = await self.session.execute(
            select(Player).where(Player.game_id == game_id, Player.tg_id == tg_id)
        )
        return res.scalar_one_or_none()

    async def remove_participant(self, game_id: int, tg_id: int) -> bool:
        res = await self.session.execute(
            delete(Player).where(Player.game_id == game_id, Player.tg_id == tg_id)
        )
        await self.session.commit()
        return (res.rowcount or 0) > 0
