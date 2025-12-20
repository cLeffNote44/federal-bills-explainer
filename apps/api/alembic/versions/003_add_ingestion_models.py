"""Add ingestion models for bills, explanations, and embeddings

NOTE: This migration was originally written to create tables that 001_initial_schema
already creates. It has been converted to a no-op to preserve the revision chain.
The actual tables are created in migration 001.

Revision ID: 003
Revises: 002
Create Date: 2024-12-30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    No-op: Tables were already created in migration 001_initial_schema.
    This migration is kept to preserve the revision chain.
    """
    pass


def downgrade() -> None:
    """
    No-op: Tables are managed by migration 001_initial_schema.
    """
    pass
