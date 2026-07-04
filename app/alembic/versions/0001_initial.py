"""initial schema — mirrors sql/01_schema.sql

Revision ID: 0001
Revises:
Create Date: 2026-07-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "polls",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("closes_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "options",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column(
            "poll_id",
            sa.BigInteger(),
            sa.ForeignKey("polls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.Text(), nullable=False),
    )
    op.create_index("idx_options_poll_id", "options", ["poll_id"])

    op.create_table(
        "votes",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column(
            "poll_id",
            sa.BigInteger(),
            sa.ForeignKey("polls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "option_id",
            sa.BigInteger(),
            sa.ForeignKey("options.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("voter_id", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("poll_id", "voter_id", name="uq_votes_poll_voter"),
    )
    op.create_index("idx_votes_poll_option", "votes", ["poll_id", "option_id"])


def downgrade() -> None:
    op.drop_index("idx_votes_poll_option", table_name="votes")
    op.drop_table("votes")
    op.drop_index("idx_options_poll_id", table_name="options")
    op.drop_table("options")
    op.drop_table("polls")
