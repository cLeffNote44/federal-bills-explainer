"""Add user features: feedback, bookmarks, tracking, topics, comments

Revision ID: 007
Revises: 006
Create Date: 2024-12-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('email_notifications', sa.Boolean(), default=True),
        sa.Column('notification_frequency', sa.String(), default='daily'),
        sa.Column('zip_code', sa.String(10), nullable=True),
        sa.Column('state', sa.String(2), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # User bookmarks
    op.create_table(
        'user_bookmarks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('bill_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('folder', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'bill_id', name='uq_user_bill_bookmark')
    )
    op.create_index('ix_user_bookmarks_user_id', 'user_bookmarks', ['user_id'])
    op.create_index('ix_user_bookmarks_bill_id', 'user_bookmarks', ['bill_id'])

    # User bill tracking for notifications
    op.create_table(
        'user_bill_tracking',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('bill_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_known_status', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'bill_id', name='uq_user_bill_tracking')
    )
    op.create_index('ix_user_bill_tracking_user_id', 'user_bill_tracking', ['user_id'])

    # Explanation feedback (thumbs up/down)
    op.create_table(
        'explanation_feedback',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('explanation_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('is_helpful', sa.Boolean(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['explanation_id'], ['explanations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'explanation_id', name='uq_user_explanation_feedback')
    )
    op.create_index('ix_explanation_feedback_explanation_id', 'explanation_feedback', ['explanation_id'])

    # Bill topics for categorization
    op.create_table(
        'bill_topics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('bill_id', sa.String(), nullable=False),
        sa.Column('topic_name', sa.String(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bill_id', 'topic_name', name='uq_bill_topic')
    )
    op.create_index('ix_bill_topics_topic_name', 'bill_topics', ['topic_name'])
    op.create_index('ix_bill_topics_bill_id', 'bill_topics', ['bill_id'])

    # Comments (community feature)
    op.create_table(
        'comments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('bill_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('parent_id', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('upvotes', sa.Integer(), default=0),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_comments_bill_id', 'comments', ['bill_id'])
    op.create_index('ix_comments_user_id', 'comments', ['user_id'])

    # Add simple_text column to explanations for ELI5 mode
    op.add_column('explanations', sa.Column('simple_text', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('explanations', 'simple_text')
    op.drop_table('comments')
    op.drop_table('bill_topics')
    op.drop_table('explanation_feedback')
    op.drop_table('user_bill_tracking')
    op.drop_table('user_bookmarks')
    op.drop_table('users')
