from dataclasses import dataclass
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.models import Game
from src.app.db.repos.game_repo import GameRepo
from src.app.db.repos.player_repo import PlayerRepo
from src.app.utils.code import generate_game_code
from src.app.utils.link import generate_link


@dataclass(frozen=True)
class GameInfoDTO:
    id: int
    name: str
    code: str
    status: str
    participants: int
    deep_link: str


class GameService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_game(self, game_name: str, money: str, owner_id: int) -> Game:
        game_repo = GameRepo(self.session)

        game_code = generate_game_code(8)
        game = await game_repo.create_game(game_name, money, game_code, owner_id)
        return game

    async def get_games_by_role(self, tg_id: int, role: str) -> list[Game]:
        game_repo = GameRepo(self.session)
        if role == "owner":
            return await game_repo.list_games_by_admin(tg_id)
        else:
            return await game_repo.list_games_by_player(tg_id)

    async def get_game_info_by_id(self, game_id: int) -> GameInfoDTO | None:
        game_repo = GameRepo(self.session)

        game = await game_repo.get_game_by_id(game_id)
        if not game:
            return None

        cnt = await game_repo.count_participants(game.id)
        link = generate_link(game.code)

        return GameInfoDTO(
            id=game.id,
            name=game.name,
            code=game.code,
            status=game.status,
            participants=cnt,
            deep_link=link,
        )

    async def lock_game(self, game_id: int) -> bool:
        repo = GameRepo(self.session)
        game = await repo.get_game_by_id(game_id)
        if not game:
            return False
        await repo.set_game_status(game_id, "locked")
        return True

    async def open_game(self, game_id: int) -> bool:
        repo = GameRepo(self.session)
        game = await repo.get_game_by_id(game_id)
        if not game:
            return False
        await repo.set_game_status(game_id, "open")
        return True

    async def drop_game(self, game_id: int) -> bool:
        repo = GameRepo(self.session)
        return await repo.delete_game(game_id)
