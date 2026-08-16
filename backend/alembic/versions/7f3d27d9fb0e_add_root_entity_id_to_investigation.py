"""Add root_entity_id to Investigation

Revision ID: 7f3d27d9fb0e
Revises: 659ec0153c30
Create Date: 2026-08-08 11:00:16.910968
"""
from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f3d27d9fb0e'
down_revision: str | None = '659ec0153c30'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('investigations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('root_entity_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key('fk_investigations_root_entity_id', 'entities', ['root_entity_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade() -> None:
    with op.batch_alter_table('investigations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_investigations_root_entity_id', type_='foreignkey')
        batch_op.drop_column('root_entity_id')
    # ### end Alembic commands ###
