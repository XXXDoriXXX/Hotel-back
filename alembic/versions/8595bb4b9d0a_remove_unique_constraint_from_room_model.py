"""Remove unique constraint from Room model

Revision ID: 8595bb4b9d0a
Revises: 
Create Date: 2025-04-14 23:01:56.031871

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8595bb4b9d0a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('rooms_room_number_key', 'rooms', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('rooms_room_number_key', 'rooms', ['room_number'])
    # ### end Alembic commands ###
