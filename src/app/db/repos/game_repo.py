from __future__ import annotations

from sqlalchemy import select, update, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.models import Game, Player


class GameRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_game(self, name: str, money: str, code: str, owner_id: int) -> Game:
        game = Game(
            owner_id=owner_id,
            code=code,
            name=name,
            money=money,
            status="open",
        )
        self.session.add(game)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(game)
        return game

    async def get_game_by_code(self, game_code: str) -> Game | None:
        res = await self.session.execute(select(Game).where(Game.code == game_code))
        return res.scalar_one_or_none()

    async def get_game_by_id(self, game_id: int) -> Game | None:
        res = await self.session.execute(select(Game).where(Game.id == game_id))
        return res.scalar_one_or_none()

    async def set_game_status(self, game_id: int, status: str) -> None:
        await self.session.execute(
            update(Game).where(Game.id == game_id).values(status=status)
        )
        await self.session.commit()

    async def list_games_by_admin(self, tg_id: int) -> list[Game]:
        stmt = select(Game).where(Game.owner_id == tg_id).order_by(Game.id.desc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def list_games_by_player(self, tg_id: int) -> list[Game]:
        stmt = (
            select(Game)
            .join(Player, Player.game_id == Game.id)
            .where(Player.tg_id == tg_id)
            .order_by(Game.id.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def count_participants(self, game_id: int) -> int:
        stmt = select(func.count(Player.id)).where(Player.game_id == game_id)
        res = await self.session.execute(stmt)
        return int(res.scalar_one())

    async def delete_game(self, game_id: int) -> bool:
        res = await self.session.execute(delete(Game).where(Game.id == game_id))
        await self.session.commit()
        return (res.rowcount or 0) > 0

