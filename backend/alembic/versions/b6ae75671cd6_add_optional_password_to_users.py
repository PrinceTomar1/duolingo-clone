"""add optional password to users

Revision ID: b6ae75671cd6
Revises: a1c7ba724667
Create Date: 2026-09-11 18:54:27.044703
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b6ae75671cd6'
down_revision: Union[str, None] = 'a1c7ba724667'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable, no server_default needed: every existing row correctly reads
    # as "no password set" (NULL), which is exactly the passwordless state
    # every seeded and previously-created account is already in.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=60), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('password_hash')
