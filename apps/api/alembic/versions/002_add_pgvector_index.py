"""add pgvector index

Revision ID: 002
Revises: 001
Create Date: 2024-01-02
"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    op.execute(
        """
        CREATE INDEX idx_embeddings_vector 
        ON embeddings 
        USING ivfflat (vector vector_l2_ops) 
        WITH (lists = 100)
        """
    )

def downgrade():
    op.drop_index('idx_embeddings_vector', table_name='embeddings')
