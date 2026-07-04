# models.py
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP


class Base(DeclarativeBase):
    pass


class Poll(Base):
    __tablename__ = "polls"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    closes_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    options: Mapped[list["Option"]] = relationship(
        back_populates="poll", cascade="all, delete-orphan"
    )
    votes: Mapped[list["Vote"]] = relationship(
        back_populates="poll", cascade="all, delete-orphan"
    )


class Option(Base):
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    poll_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("polls.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(Text, nullable=False)

    poll: Mapped[Poll] = relationship(back_populates="options")
    votes: Mapped[list["Vote"]] = relationship(
        back_populates="option", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_options_poll_id", "poll_id"),)


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    poll_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("polls.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("options.id", ondelete="CASCADE"),
        nullable=False,
    )
    voter_id: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    poll: Mapped[Poll] = relationship(back_populates="votes")
    option: Mapped[Option] = relationship(back_populates="votes")

    __table_args__ = (
        UniqueConstraint("poll_id", "voter_id", name="uq_votes_poll_voter"),
        Index("idx_votes_poll_option", "poll_id", "option_id"),
    )
