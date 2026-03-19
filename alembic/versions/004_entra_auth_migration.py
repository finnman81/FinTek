"""Rename clerk_user_id to entra_object_id on users table.

Revision ID: 004
Revises: 003
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_users_clerk_user_id", table_name="users")
    op.alter_column("users", "clerk_user_id", new_column_name="entra_object_id")
    op.create_index("ix_users_entra_object_id", "users", ["entra_object_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_entra_object_id", table_name="users")
    op.alter_column("users", "entra_object_id", new_column_name="clerk_user_id")
    op.create_index("ix_users_clerk_user_id", "users", ["clerk_user_id"], unique=True)
