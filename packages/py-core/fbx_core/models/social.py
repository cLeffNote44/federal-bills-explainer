"""
User authentication and authorization models.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """User model for authentication and profile."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile fields
    full_name = Column(String(255))
    bio = Column(Text)
    avatar_url = Column(String(500))
    location = Column(String(100))
    website = Column(String(255))

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # Reputation
    reputation = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Email verification
    verification_token = Column(String(255))
    verification_sent_at = Column(DateTime)
    verified_at = Column(DateTime)

    # Password reset
    reset_token = Column(String(255))
    reset_sent_at = Column(DateTime)


class Bookmark(Base):
    """Bill bookmark model."""

    __tablename__ = "bookmarks"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    bill_id = Column(String(50), nullable=False, index=True)

    notes = Column(Text)
    tags = Column(Text)  # JSON array of tags

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Collection(Base):
    """Bill collection model."""

    __tablename__ = "collections"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CollectionItem(Base):
    """Items in a collection."""

    __tablename__ = "collection_items"

    id = Column(String(36), primary_key=True)
    collection_id = Column(String(36), nullable=False, index=True)
    bill_id = Column(String(50), nullable=False)

    notes = Column(Text)
    order = Column(Integer, default=0)

    added_at = Column(DateTime, default=datetime.utcnow)


class Comment(Base):
    """Comment model for bills."""

    __tablename__ = "comments"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    bill_id = Column(String(50), nullable=False, index=True)
    parent_id = Column(String(36))  # For threaded comments

    content = Column(Text, nullable=False)

    # Moderation
    is_deleted = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    flag_count = Column(Integer, default=0)

    # Voting
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)


class Vote(Base):
    """Vote model for comments."""

    __tablename__ = "votes"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    comment_id = Column(String(36), nullable=False, index=True)

    vote_type = Column(String(10), nullable=False)  # 'upvote' or 'downvote'

    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    """Notification model."""

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)

    type = Column(String(50), nullable=False)  # 'comment_reply', 'bill_update', etc.
    title = Column(String(255), nullable=False)
    message = Column(Text)
    link = Column(String(500))

    data = Column(Text)  # JSON data

    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)


class BillWatch(Base):
    """Track bills for notifications."""

    __tablename__ = "bill_watches"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    bill_id = Column(String(50), nullable=False, index=True)

    notify_email = Column(Boolean, default=True)
    notify_in_app = Column(Boolean, default=True)
    webhook_url = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)
    last_notified = Column(DateTime)
