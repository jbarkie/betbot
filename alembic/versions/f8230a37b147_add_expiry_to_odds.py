"""Add expiry to odds

Revision ID: f8230a37b147
Revises: a5d3e5750b30
Create Date: 2024-04-02 20:24:52.014030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8230a37b147'
down_revision: Union[str, None] = 'a5d3e5750b30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('odds', sa.Column('expires', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('odds', 'expires')
    # ### end Alembic commands ###