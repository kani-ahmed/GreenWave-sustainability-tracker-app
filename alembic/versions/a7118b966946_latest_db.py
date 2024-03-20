"""latest db

Revision ID: a7118b966946
Revises: 8f899c8b0c67
Create Date: 2024-03-18 01:45:53.430498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7118b966946'
down_revision: Union[str, None] = '8f899c8b0c67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
