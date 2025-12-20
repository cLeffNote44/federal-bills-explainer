"""Add performance indexes for optimized querying

Revision ID: 004
Revises: 003
Create Date: 2025-01-10

NOTE: Updated to use correct column names from 001_initial_schema.py
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for frequently queried columns.

    Uses column names from 001_initial_schema.py:
    - bills: id, congress, bill_type, number, title, summary, status,
             introduced_date, latest_action_date, congress_url, public_law_number,
             sponsor, committees, subjects, cosponsors_count, last_fetched_at
    - explanations: id, bill_id, model_name, generated_at, text, version
    - embeddings: id, bill_id, content_kind, model_name, content_hash, vector
    """

    # Bills table indexes
    # Index for date range queries (commonly used in sync operations)
    op.create_index(
        'ix_bills_latest_action_date',
        'bills',
        ['latest_action_date'],
        postgresql_using='btree'
    )

    # Index for public_law_number lookups (for finding enacted bills)
    op.create_index(
        'ix_bills_public_law_number',
        'bills',
        ['public_law_number'],
        postgresql_using='btree',
        postgresql_where=text('public_law_number IS NOT NULL')
    )

    # Composite index for congress/type/number lookups
    op.create_index(
        'ix_bills_congress_type_number',
        'bills',
        ['congress', 'bill_type', 'number'],
        postgresql_using='btree'
    )

    # Index for last_fetched_at (for incremental sync)
    op.create_index(
        'ix_bills_last_fetched_at',
        'bills',
        ['last_fetched_at'],
        postgresql_using='btree'
    )

    # Index for status filtering
    op.create_index(
        'ix_bills_status',
        'bills',
        ['status'],
        postgresql_using='btree',
        postgresql_where=text('status IS NOT NULL')
    )

    # Full text search index on title and summary
    op.execute("""
        CREATE INDEX ix_bills_text_search
        ON bills
        USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(summary, '')))
    """)

    # Explanations table indexes
    # Index for generated_at (for getting recent explanations)
    op.create_index(
        'ix_explanations_generated_at',
        'explanations',
        ['generated_at'],
        postgresql_using='btree'
    )

    # Index for model_name (for filtering by model)
    op.create_index(
        'ix_explanations_model_name',
        'explanations',
        ['model_name'],
        postgresql_using='btree'
    )

    # Embeddings table indexes
    # Index for content_kind (for filtering by type)
    op.create_index(
        'ix_embeddings_content_kind',
        'embeddings',
        ['content_kind'],
        postgresql_using='btree'
    )

    # Index for model_name in embeddings
    op.create_index(
        'ix_embeddings_model_name',
        'embeddings',
        ['model_name'],
        postgresql_using='btree'
    )

    # Analyze tables to update statistics
    op.execute('ANALYZE bills;')
    op.execute('ANALYZE explanations;')
    op.execute('ANALYZE embeddings;')


def downgrade() -> None:
    """Remove performance indexes."""

    # Drop embeddings indexes
    op.drop_index('ix_embeddings_model_name', 'embeddings')
    op.drop_index('ix_embeddings_content_kind', 'embeddings')

    # Drop explanations indexes
    op.drop_index('ix_explanations_model_name', 'explanations')
    op.drop_index('ix_explanations_generated_at', 'explanations')

    # Drop bills indexes
    op.execute('DROP INDEX IF EXISTS ix_bills_text_search;')
    op.drop_index('ix_bills_status', 'bills')
    op.drop_index('ix_bills_last_fetched_at', 'bills')
    op.drop_index('ix_bills_congress_type_number', 'bills')
    op.drop_index('ix_bills_public_law_number', 'bills')
    op.drop_index('ix_bills_latest_action_date', 'bills')
