"""Database models for Federal Bills Explainer."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Float,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Bill(Base):
    """Bill model."""
    
    __tablename__ = "bills"
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String(50), unique=True, nullable=False, index=True)
    congress = Column(Integer, nullable=False)
    bill_type = Column(String(20), nullable=False)
    bill_number = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    short_title = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    law_number = Column(String(50), nullable=True)
    latest_action_date = Column(Date, nullable=True)
    latest_action_text = Column(Text, nullable=True)
    sponsor = Column(String(255), nullable=True)
    policy_area = Column(String(255), nullable=True)
    text_url = Column(Text, nullable=True)
    govtrack_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    explanations = relationship("Explanation", back_populates="bill", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Bill(external_id='{self.external_id}', title='{self.title[:50]}...')>"


class Explanation(Base):
    """Explanation model."""
    
    __tablename__ = "explanations"
    
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    explanation_text = Column(Text, nullable=False)
    model_name = Column(String(100), nullable=False)
    word_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    bill = relationship("Bill", back_populates="explanations")
    embeddings = relationship("Embedding", back_populates="explanation", cascade="all, delete-orphan")
    
    # Unique constraint on bill_id and model_name
    __table_args__ = (
        UniqueConstraint("bill_id", "model_name", name="uq_bill_model"),
        Index("ix_explanation_bill_model", "bill_id", "model_name"),
    )
    
    def __repr__(self):
        return f"<Explanation(bill_id={self.bill_id}, model='{self.model_name}')>"


class Embedding(Base):
    """Embedding model for vector search."""
    
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True)
    entity_type = Column(String(50), nullable=False)  # 'bill' or 'explanation'
    entity_id = Column(Integer, nullable=False)  # ID of the bill or explanation
    explanation_id = Column(Integer, ForeignKey("explanations.id"), nullable=True)
    vector = Column(Vector(384), nullable=False)  # 384 dimensions for all-MiniLM-L6-v2
    model_name = Column(String(100), nullable=False)
    text_used = Column(Text, nullable=False)  # Text that was embedded
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    explanation = relationship("Explanation", back_populates="embeddings")
    
    # Indexes for efficient search
    __table_args__ = (
        Index("ix_embedding_entity", "entity_type", "entity_id"),
        Index("ix_embedding_vector", "vector", postgresql_using="ivfflat"),
    )
    
    def __repr__(self):
        return f"<Embedding(entity_type='{self.entity_type}', entity_id={self.entity_id})>"
