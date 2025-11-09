"""Add ingestion models for bills, explanations, and embeddings

Revision ID: 003
Revises: 002
Create Date: 2024-12-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create bills table
    op.create_table(
        'bills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(50), nullable=False),
        sa.Column('congress', sa.Integer(), nullable=False),
        sa.Column('bill_type', sa.String(20), nullable=False),
        sa.Column('bill_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('short_title', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('law_number', sa.String(50), nullable=True),
        sa.Column('latest_action_date', sa.Date(), nullable=True),
        sa.Column('latest_action_text', sa.Text(), nullable=True),
        sa.Column('sponsor', sa.String(255), nullable=True),
        sa.Column('policy_area', sa.String(255), nullable=True),
        sa.Column('text_url', sa.Text(), nullable=True),
        sa.Column('govtrack_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id')
    )
    op.create_index('ix_bills_external_id', 'bills', ['external_id'])
    
    # Create explanations table
    op.create_table(
        'explanations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bill_id', sa.Integer(), nullable=False),
        sa.Column('explanation_text', sa.Text(), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bill_id', 'model_name', name='uq_bill_model')
    )
    op.create_index('ix_explanation_bill_model', 'explanations', ['bill_id', 'model_name'])
    
    # Create embeddings table with pgvector
    op.create_table(
        'embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('explanation_id', sa.Integer(), nullable=True),
        sa.Column('vector', Vector(384), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('text_used', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['explanation_id'], ['explanations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_embedding_entity', 'embeddings', ['entity_type', 'entity_id'])
    
    # Create vector similarity search index
    op.execute('CREATE INDEX ix_embedding_vector ON embeddings USING ivfflat (vector vector_l2_ops) WITH (lists = 100);')


def downgrade() -> None:
    op.drop_index('ix_embedding_vector', 'embeddings')
    op.drop_index('ix_embedding_entity', 'embeddings')
    op.drop_table('embeddings')
    
    op.drop_index('ix_explanation_bill_model', 'explanations')
    op.drop_table('explanations')
    
    op.drop_index('ix_bills_external_id', 'bills')
    op.drop_table('bills')
