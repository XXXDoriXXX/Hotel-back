"""Add is_owner column to people

Revision ID: 08cef15f5d5f
Revises: 7fa0a2698556
Create Date: 2024-12-10 20:31:28.878058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08cef15f5d5f'
down_revision: Union[str, None] = '7fa0a2698556'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Додаємо стовпець з тимчасовим значенням за замовчуванням False
    op.add_column('people', sa.Column('is_owner', sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()))
    # Після цього видаляємо значення за замовчуванням
    op.alter_column('people', 'is_owner', server_default=None)

def downgrade():
    op.drop_column('people', 'is_owner')
