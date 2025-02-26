"""Add employees table

Revision ID: 994122d4fda0
Revises: 08cef15f5d5f
Create Date: 2024-12-13 12:00:26.784692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '994122d4fda0'
down_revision: Union[str, None] = '08cef15f5d5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('person_id', sa.Integer(), sa.ForeignKey('people.id'), unique=True, nullable=False),
        sa.Column('hotel_id', sa.Integer(), sa.ForeignKey('hotels.id'), nullable=False),
        sa.Column('position', sa.String(), nullable=False),
        sa.Column('salary', sa.Float(), nullable=False),
        sa.Column('work_experience', sa.Integer(), nullable=False),
        sa.Column('is_vacation', sa.Boolean(), default=False)
    )

def downgrade():
    op.drop_table('employees')
