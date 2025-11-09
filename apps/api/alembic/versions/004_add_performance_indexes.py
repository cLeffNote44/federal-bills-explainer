"""Add performance indexes for optimized querying

Revision ID: 004
Revises: 003
Create Date: 2025-01-10

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
    """Add performance indexes for frequently queried columns."""
    
    # Bills table indexes
    # Index for date range queries (commonly used in sync operations)
    op.create_index(
        'ix_bills_latest_action_date', 
        'bills', 
        ['latest_action_date'],
        postgresql_using='btree'
    )
    
    # Index for law number lookups (for finding enacted bills)
    op.create_index(
        'ix_bills_law_number', 
        'bills', 
        ['law_number'],
        postgresql_using='btree',
        postgresql_where=text('law_number IS NOT NULL')
    )
    
    # Composite index for congress/type/number lookups
    op.create_index(
        'ix_bills_congress_type_number', 
        'bills', 
        ['congress', 'bill_type', 'bill_number'],
        postgresql_using='btree'
    )
    
    # Index for created_at (for incremental sync)
    op.create_index(
        'ix_bills_created_at', 
        'bills', 
        ['created_at'],
        postgresql_using='btree'
    )
    
    # Index for policy area filtering
    op.create_index(
        'ix_bills_policy_area', 
        'bills', 
        ['policy_area'],
        postgresql_using='btree',
        postgresql_where=text('policy_area IS NOT NULL')
    )
    
    # Full text search index on title and summary
    op.execute("""
        CREATE INDEX ix_bills_text_search 
        ON bills 
        USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(short_title, '') || ' ' || coalesce(summary, '')))
    """)
    
    # Explanations table indexes
    # Index for created_at (for getting recent explanations)
    op.create_index(
        'ix_explanations_created_at', 
        'explanations', 
        ['created_at'],
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
    # Index for explanation_id foreign key (if not already created by FK constraint)
    op.create_index(
        'ix_embeddings_explanation_id', 
        'embeddings', 
        ['explanation_id'],
        postgresql_using='btree',
        postgresql_where=text('explanation_id IS NOT NULL')
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
    
    print("✅ Performance indexes created successfully")
    print("📊 Table statistics updated")


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Drop embeddings indexes
    op.drop_index('ix_embeddings_model_name', 'embeddings')
    op.drop_index('ix_embeddings_explanation_id', 'embeddings')
    
    # Drop explanations indexes
    op.drop_index('ix_explanations_model_name', 'explanations')
    op.drop_index('ix_explanations_created_at', 'explanations')
    
    # Drop bills indexes
    op.execute('DROP INDEX IF EXISTS ix_bills_text_search;')
    op.drop_index('ix_bills_policy_area', 'bills')
    op.drop_index('ix_bills_created_at', 'bills')
    op.drop_index('ix_bills_congress_type_number', 'bills')
    op.drop_index('ix_bills_law_number', 'bills')
    op.drop_index('ix_bills_latest_action_date', 'bills')