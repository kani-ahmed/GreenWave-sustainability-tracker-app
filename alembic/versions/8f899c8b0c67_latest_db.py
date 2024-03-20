"""latest db

Revision ID: 8f899c8b0c67
Revises: 642acd177da5
Create Date: 2024-03-18 01:41:02.550324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f899c8b0c67'
down_revision: Union[str, None] = '642acd177da5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
