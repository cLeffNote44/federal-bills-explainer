"""Add job tracking for ingestion monitoring

Revision ID: 005
Revises: 004
Create Date: 2025-01-10

NOTE: Using String for status instead of ENUM to avoid migration complexities.
Valid values: 'pending', 'running', 'completed', 'failed', 'cancelled'
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables for job tracking and monitoring."""

    # Create ingestion_jobs table
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(100), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False, server_default='sync'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Job configuration
        sa.Column('config', postgresql.JSONB, nullable=True),
        sa.Column('from_date', sa.Date(), nullable=True),
        sa.Column('to_date', sa.Date(), nullable=True),
        sa.Column('max_records', sa.Integer(), nullable=True),
        sa.Column('dry_run', sa.Boolean(), nullable=False, server_default='false'),

        # Metrics
        sa.Column('total_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_records', sa.Integer(), nullable=False, server_default='0'),

        # Performance metrics
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('avg_record_time_ms', sa.Float(), nullable=True),
        sa.Column('api_calls_made', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('api_errors', sa.Integer(), nullable=False, server_default='0'),

        # Error tracking
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB, nullable=True),
        sa.Column('last_error_at', sa.DateTime(), nullable=True),

        # Additional metadata
        sa.Column('triggered_by', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )

    # Add check constraint for status values
    op.execute("""
        ALTER TABLE ingestion_jobs
        ADD CONSTRAINT ck_job_status
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
    """)

    # Create indexes for job tracking
    op.create_index('ix_ingestion_jobs_job_id', 'ingestion_jobs', ['job_id'])
    op.create_index('ix_ingestion_jobs_status', 'ingestion_jobs', ['status'])
    op.create_index('ix_ingestion_jobs_created_at', 'ingestion_jobs', ['created_at'])
    op.create_index('ix_ingestion_jobs_started_at', 'ingestion_jobs', ['started_at'])
    op.create_index(
        'ix_ingestion_jobs_running',
        'ingestion_jobs',
        ['status'],
        postgresql_where=sa.text("status = 'running'")
    )

    # Create job_logs table for detailed logging
    op.create_table(
        'job_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(100), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', postgresql.JSONB, nullable=True),
        sa.Column('record_id', sa.String(100), nullable=True),

        sa.ForeignKeyConstraint(['job_id'], ['ingestion_jobs.job_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for job_logs
    op.create_index('ix_job_logs_job_id', 'job_logs', ['job_id'])
    op.create_index('ix_job_logs_timestamp', 'job_logs', ['timestamp'])
    op.create_index('ix_job_logs_level', 'job_logs', ['level'])
    op.create_index(
        'ix_job_logs_errors',
        'job_logs',
        ['job_id', 'timestamp'],
        postgresql_where=sa.text("level = 'ERROR'")
    )

    # Create job_metrics table for time-series metrics
    op.create_table(
        'job_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(100), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('tags', postgresql.JSONB, nullable=True),

        sa.ForeignKeyConstraint(['job_id'], ['ingestion_jobs.job_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for job_metrics
    op.create_index('ix_job_metrics_job_id', 'job_metrics', ['job_id'])
    op.create_index('ix_job_metrics_timestamp', 'job_metrics', ['timestamp'])
    op.create_index('ix_job_metrics_name', 'job_metrics', ['metric_name'])

    # Create view for job statistics
    op.execute("""
        CREATE OR REPLACE VIEW v_job_statistics AS
        SELECT
            DATE(created_at) as date,
            job_type,
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
            COUNT(CASE WHEN status = 'running' THEN 1 END) as running_jobs,
            COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_jobs,
            AVG(CASE WHEN status = 'completed' THEN duration_seconds END) as avg_duration,
            SUM(CASE WHEN status = 'completed' THEN processed_records ELSE 0 END) as total_processed,
            SUM(CASE WHEN status = 'completed' THEN failed_records ELSE 0 END) as total_failed,
            AVG(CASE WHEN status = 'completed' AND processed_records > 0
                THEN processed_records::float / duration_seconds
                ELSE NULL END) as avg_throughput
        FROM ingestion_jobs
        GROUP BY DATE(created_at), job_type
        ORDER BY date DESC;
    """)


def downgrade() -> None:
    """Remove job tracking tables."""

    # Drop view
    op.execute("DROP VIEW IF EXISTS v_job_statistics;")

    # Drop metrics table
    op.drop_index('ix_job_metrics_name', 'job_metrics')
    op.drop_index('ix_job_metrics_timestamp', 'job_metrics')
    op.drop_index('ix_job_metrics_job_id', 'job_metrics')
    op.drop_table('job_metrics')

    # Drop logs table
    op.drop_index('ix_job_logs_errors', 'job_logs')
    op.drop_index('ix_job_logs_level', 'job_logs')
    op.drop_index('ix_job_logs_timestamp', 'job_logs')
    op.drop_index('ix_job_logs_job_id', 'job_logs')
    op.drop_table('job_logs')

    # Drop jobs table
    op.drop_index('ix_ingestion_jobs_running', 'ingestion_jobs')
    op.drop_index('ix_ingestion_jobs_started_at', 'ingestion_jobs')
    op.drop_index('ix_ingestion_jobs_created_at', 'ingestion_jobs')
    op.drop_index('ix_ingestion_jobs_status', 'ingestion_jobs')
    op.drop_index('ix_ingestion_jobs_job_id', 'ingestion_jobs')
    op.drop_table('ingestion_jobs')
