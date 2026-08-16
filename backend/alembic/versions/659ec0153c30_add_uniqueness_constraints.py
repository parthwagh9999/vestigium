"""Add uniqueness constraints

Revision ID: 659ec0153c30
Revises: 
Create Date: 2026-08-08 10:47:25.466106
"""
from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '659ec0153c30'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('entities', schema=None) as batch_op:
        batch_op.create_unique_constraint('uix_investigation_entity_type_value', ['investigation_id', 'entity_type', 'value'])
    
    with op.batch_alter_table('entity_relationships', schema=None) as batch_op:
        batch_op.create_unique_constraint('uix_investigation_source_target_type', ['investigation_id', 'source_entity_id', 'target_entity_id', 'relationship_type'])
    # ### end Alembic commands ###


def downgrade() -> None:
    with op.batch_alter_table('entity_relationships', schema=None) as batch_op:
        batch_op.drop_constraint('uix_investigation_source_target_type', type_='unique')
        
    with op.batch_alter_table('entities', schema=None) as batch_op:
        batch_op.drop_constraint('uix_investigation_entity_type_value', type_='unique')
    # ### end Alembic commands ###
