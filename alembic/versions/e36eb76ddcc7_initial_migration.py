"""Initial migration

Revision ID: e36eb76ddcc7
Revises: 
Create Date: 2024-03-29 16:54:27.103545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e36eb76ddcc7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('odds',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('time', sa.DateTime(), nullable=True),
    sa.Column('home_odds', sa.String(), nullable=True),
    sa.Column('away_odds', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('odds')
    # ### end Alembic commands ###