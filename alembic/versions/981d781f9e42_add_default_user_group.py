"""Add default user group

Revision ID: 981d781f9e42
Revises: 9c7557680a00
Create Date: 2025-09-11 18:57:24.666395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '981d781f9e42'
down_revision: Union[str, Sequence[str], None] = '9c7557680a00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(
        """
        INSERT INTO user_groups (name)
        SELECT 'USER' WHERE NOT EXISTS (
            SELECT 1 FROM user_groups WHERE name = 'USER'
        );
        """
    )
    op.execute(
        """
        INSERT INTO user_groups (name)
        SELECT 'MODERATOR' WHERE NOT EXISTS (
            SELECT 1 FROM user_groups WHERE name = 'MODERATOR'
        );
        """
    )
    op.execute(
        """
        INSERT INTO user_groups (name)
        SELECT 'ADMIN' WHERE NOT EXISTS (
            SELECT 1 FROM user_groups WHERE name = 'ADMIN'
        );
        """
    )


def downgrade():
    op.execute("DELETE FROM user_groups WHERE name='USER'")
    op.execute("DELETE FROM user_groups WHERE name='MODERATOR'")
    op.execute("DELETE FROM user_groups WHERE name='ADMIN'")