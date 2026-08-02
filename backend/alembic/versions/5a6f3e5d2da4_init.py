"""init

Revision ID: 5a6f3e5d2da4
Revises: 
Create Date: 2026-08-01 17:14:47.558366

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '5a6f3e5d2da4'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
