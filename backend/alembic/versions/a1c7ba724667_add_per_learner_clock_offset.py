"""add per-learner clock offset

Revision ID: a1c7ba724667
Revises: c89f99c0901d
Create Date: 2026-09-08 09:34:05.332417
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1c7ba724667'
down_revision: Union[str, None] = 'c89f99c0901d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default backfills every existing learner's row to 0 (real time) in
    # one statement -- required on Postgres, which rejects adding a NOT NULL
    # column to a populated table with no default.
    with op.batch_alter_table('user_stats', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('clock_offset_seconds', sa.Integer(), nullable=False, server_default='0')
        )


def downgrade() -> None:
    with op.batch_alter_table('user_stats', schema=None) as batch_op:
        batch_op.drop_column('clock_offset_seconds')
