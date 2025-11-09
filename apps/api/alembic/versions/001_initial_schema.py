"""initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    op.create_table('bills',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('congress', sa.Integer(), nullable=False),
        sa.Column('bill_type', sa.String(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('introduced_date', sa.Date(), nullable=True),
        sa.Column('latest_action_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('congress_url', sa.Text(), nullable=True),
        sa.Column('public_law_number', sa.String(), nullable=True),
        sa.Column('sponsor', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('committees', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('subjects', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('cosponsors_count', sa.Integer(), nullable=True),
        sa.Column('last_fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bill_type', 'number', 'congress', name='uq_bill_identity')
    )
    
    op.create_table('ingestion_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('explanations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('bill_id', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('embeddings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('bill_id', sa.String(), nullable=False),
        sa.Column('content_kind', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=False),
        sa.Column('vector', Vector(384), nullable=False),
        sa.CheckConstraint("content_kind IN ('document')", name='ck_content_kind'),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_hash', 'model_name', name='uq_embedding_cache')
    )
    op.create_index(op.f('ix_embeddings_content_hash'), 'embeddings', ['content_hash'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_embeddings_content_hash'), table_name='embeddings')
    op.drop_table('embeddings')
    op.drop_table('explanations')
    op.drop_table('ingestion_state')
    op.drop_table('bills')
    op.execute("DROP EXTENSION IF EXISTS vector")
