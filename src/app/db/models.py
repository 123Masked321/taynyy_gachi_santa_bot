from sqlalchemy.orm import Mapped, relationship, mapped_column, DeclarativeBase
from sqlalchemy import ForeignKey, UniqueConstraint, CheckConstraint, BigInteger


class Base(DeclarativeBase):
    pass


class Game(Base):
    __tablename__ = 'games'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    money: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    players: Mapped[list["Player"]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",
    )


class Player(Base):
    __tablename__ = 'players'
    __table_args__ = (
        UniqueConstraint("game_id", "tg_id", name="unique_players_game"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(nullable=False)

    game: Mapped["Game"] = relationship("Game", back_populates="players")


class Assignment(Base):
    __tablename__ = 'assignments'
    __table_args__ = (
        UniqueConstraint("game_id", "giver_id", name="unique_assignment_game_giver"),
        UniqueConstraint("game_id", "receiver_id", name="unique_assignment_game_receiver"),
        CheckConstraint("giver_id <> receiver_id", name="check_not_self"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    giver_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)