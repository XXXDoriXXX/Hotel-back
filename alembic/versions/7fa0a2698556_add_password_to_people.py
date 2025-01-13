"""Add password to people

Revision ID: 7fa0a2698556
Revises: a1ec2d61321a
Create Date: 2024-12-10 14:36:32.744611

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fa0a2698556'
down_revision: Union[str, None] = 'a1ec2d61321a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Додаємо новий стовпець
    op.add_column('people', sa.Column('password', sa.String(), nullable=True))

    # Заповнюємо всі існуючі записи значенням за замовчуванням
    op.execute("UPDATE people SET password = 'default_password'")

    # Робимо стовпець обов'язковим
    op.alter_column('people', 'password', nullable=False)


def downgrade():
    op.drop_column('people', 'password')

