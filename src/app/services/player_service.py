from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.models import Game, Player
from src.app.db.repos.game_repo import GameRepo
from src.app.db.repos.player_repo import PlayerRepo


@dataclass(frozen=True)
class JoinPrecheckResult:
    ok: bool
    reason: str
    game: Game | None = None


class PlayerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def precheck_join_by_code(
            self,
            code: str,
            tg_id: int,
            require_collecting: bool = True,
    ) -> JoinPrecheckResult:
        game_repo = GameRepo(self.session)
        player_repo = PlayerRepo(self.session)

        game = await game_repo.get_game_by_code(code)
        if not game:
            return JoinPrecheckResult(ok=False, reason="not_found", game=None)

        if require_collecting and getattr(game, "status", None) != "open":
            return JoinPrecheckResult(ok=False, reason="closed", game=game)

        existing = await player_repo.get_player_by_tg(game.id, tg_id)
        if existing:
            return JoinPrecheckResult(ok=False, reason="already_joined", game=game)

        return JoinPrecheckResult(ok=True, reason="ok", game=game)

    async def join_game_by_code(
            self,
            code: str,
            tg_id: int,
            name: str,
            username: str = ""
    ) -> Player:
        game_repo = GameRepo(self.session)
        player_repo = PlayerRepo(self.session)

        game = await game_repo.get_game_by_code(code)

        created = await player_repo.add_participant(
            game_id=game.id,
            tg_id=tg_id,
            name=name,
            username=username or "",
        )
        return created

    async def leave_game(self, game_id: int, tg_id: int) -> bool:
        game_repo = GameRepo(self.session)
        game = await game_repo.get_game_by_id(game_id)
        if not game:
            return False

        if game.owner_id == tg_id:
            return False

        player_repo = PlayerRepo(self.session)
        return await player_repo.remove_participant(game_id, tg_id)

    async def get_list_participants(self, game_id: int) -> list[Player]:
        repo = PlayerRepo(self.session)
        return await repo.list_participants(game_id)
