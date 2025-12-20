"""Add incremental sync tracking

Revision ID: 006
Revises: 005
Create Date: 2025-01-10

NOTE: Updated to use correct column types (bills.id is String/UUID, not Integer)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add tables and columns for incremental sync tracking."""

    # Create sync_state table to track last successful sync
    op.create_table(
        'sync_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_type', sa.String(50), nullable=False),
        sa.Column('last_sync_at', sa.DateTime(), nullable=False),
        sa.Column('last_successful_job_id', sa.String(100), nullable=True),
        sa.Column('last_bill_date', sa.Date(), nullable=True),
        sa.Column('last_bill_id', sa.String(50), nullable=True),
        sa.Column('total_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sync_type')
    )

    # Add version tracking to bills table
    op.add_column('bills', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('bills', sa.Column('last_modified', sa.DateTime(), nullable=True))
    op.add_column('bills', sa.Column('checksum', sa.String(64), nullable=True))

    # Create bill_versions table for history
    # NOTE: bill_id is String to match bills.id (UUID)
    op.create_table(
        'bill_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bill_id', sa.String(), nullable=False),  # String to match bills.id
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('latest_action_text', sa.Text(), nullable=True),
        sa.Column('change_type', sa.String(50), nullable=True),  # 'amendment', 'status_change', 'content_update'
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('checksum', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for version tracking
    op.create_index('ix_sync_state_sync_type', 'sync_state', ['sync_type'])
    op.create_index('ix_sync_state_last_sync', 'sync_state', ['last_sync_at'])
    op.create_index('ix_bills_version', 'bills', ['version'])
    op.create_index('ix_bills_last_modified', 'bills', ['last_modified'])
    op.create_index('ix_bill_versions_bill_id', 'bill_versions', ['bill_id'])
    op.create_index('ix_bill_versions_created_at', 'bill_versions', ['created_at'])


def downgrade() -> None:
    """Remove incremental sync tracking."""

    # Drop indexes
    op.drop_index('ix_bill_versions_created_at', 'bill_versions')
    op.drop_index('ix_bill_versions_bill_id', 'bill_versions')
    op.drop_index('ix_bills_last_modified', 'bills')
    op.drop_index('ix_bills_version', 'bills')
    op.drop_index('ix_sync_state_last_sync', 'sync_state')
    op.drop_index('ix_sync_state_sync_type', 'sync_state')

    # Drop tables
    op.drop_table('bill_versions')
    op.drop_table('sync_state')

    # Drop columns
    op.drop_column('bills', 'checksum')
    op.drop_column('bills', 'last_modified')
    op.drop_column('bills', 'version')
