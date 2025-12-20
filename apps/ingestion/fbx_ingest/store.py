"""Storage persistence for bills, explanations, and embeddings."""

import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from rich.console import Console

from fbx_core.db import init_database, get_session
from fbx_core.models import Bill, Explanation, Embedding
from .types import BillDTO, ExplanationDTO, EmbeddingDTO

logger = logging.getLogger(__name__)
console = Console()


class StorageManager:
    """Manage storage operations for ingestion."""
    
    def __init__(self, database_url: str):
        """Initialize storage manager."""
        self.database_url = database_url
        init_database(database_url)
        self.stats = {
            "bills_created": 0,
            "bills_updated": 0,
            "explanations_created": 0,
            "explanations_updated": 0,
            "embeddings_created": 0
        }
        
    def upsert_bill(self, session: Session, bill_dto: BillDTO) -> Tuple[Bill, bool]:
        """Upsert a bill, returning the bill and whether it was created."""
        # Check if bill exists
        existing_bill = session.query(Bill).filter_by(
            external_id=bill_dto.external_id
        ).first()
        
        if existing_bill:
            # Update existing bill
            for field in ["title", "short_title", "summary", "law_number", 
                         "latest_action_date", "latest_action_text", "sponsor",
                         "policy_area", "text_url", "govtrack_url"]:
                value = getattr(bill_dto, field)
                if value is not None:
                    setattr(existing_bill, field, value)
            
            self.stats["bills_updated"] += 1
            return existing_bill, False
        else:
            # Create new bill
            new_bill = Bill(
                external_id=bill_dto.external_id,
                congress=bill_dto.congress,
                bill_type=bill_dto.bill_type,
                bill_number=bill_dto.bill_number,
                title=bill_dto.title,
                short_title=bill_dto.short_title,
                summary=bill_dto.summary,
                law_number=bill_dto.law_number,
                latest_action_date=bill_dto.latest_action_date,
                latest_action_text=bill_dto.latest_action_text,
                sponsor=bill_dto.sponsor,
                policy_area=bill_dto.policy_area,
                text_url=bill_dto.text_url,
                govtrack_url=bill_dto.govtrack_url
            )
            session.add(new_bill)
            session.flush()  # Get the ID
            
            self.stats["bills_created"] += 1
            return new_bill, True
            
    def upsert_explanation(
        self, 
        session: Session, 
        bill_id: int, 
        explanation_dto: ExplanationDTO
    ) -> Tuple[Explanation, bool]:
        """Upsert an explanation, returning the explanation and whether it was created."""
        # Check if explanation exists for this bill and model
        existing_explanation = session.query(Explanation).filter_by(
            bill_id=bill_id,
            model_name=explanation_dto.model_name
        ).first()
        
        if existing_explanation:
            # Update existing explanation
            existing_explanation.explanation_text = explanation_dto.explanation_text
            existing_explanation.word_count = explanation_dto.word_count
            
            self.stats["explanations_updated"] += 1
            return existing_explanation, False
        else:
            # Create new explanation
            new_explanation = Explanation(
                bill_id=bill_id,
                explanation_text=explanation_dto.explanation_text,
                model_name=explanation_dto.model_name,
                word_count=explanation_dto.word_count
            )
            session.add(new_explanation)
            session.flush()  # Get the ID
            
            self.stats["explanations_created"] += 1
            return new_explanation, True
            
    def insert_embedding(
        self,
        session: Session,
        embedding_dto: EmbeddingDTO,
        explanation_id: Optional[int] = None
    ) -> Embedding:
        """Insert a new embedding."""
        new_embedding = Embedding(
            entity_type=embedding_dto.entity_type,
            entity_id=int(embedding_dto.entity_id),
            explanation_id=explanation_id,
            vector=embedding_dto.vector,
            model_name=embedding_dto.model_name,
            text_used=embedding_dto.text_used
        )
        session.add(new_embedding)
        session.flush()
        
        self.stats["embeddings_created"] += 1
        return new_embedding
        
    def persist_bill_package(
        self,
        bill_dto: BillDTO,
        explanation_dto: ExplanationDTO,
        embedding_dto: EmbeddingDTO
    ) -> bool:
        """Persist a complete bill package (bill, explanation, embedding)."""
        try:
            # Use session from global database
            for session in get_session():
                # Upsert bill
                bill, bill_created = self.upsert_bill(session, bill_dto)
                
                # Upsert explanation
                explanation, explanation_created = self.upsert_explanation(
                    session, bill.id, explanation_dto
                )
                
                # Only create embedding if explanation is new or updated
                if explanation_created or explanation.updated_at == session.query(Explanation).get(explanation.id).updated_at:
                    # Delete old embeddings for this explanation
                    session.query(Embedding).filter_by(
                        entity_type="explanation",
                        entity_id=explanation.id
                    ).delete()
                    
                    # Insert new embedding
                    embedding_dto.entity_id = str(explanation.id)
                    self.insert_embedding(session, embedding_dto, explanation.id)
                
                # Commit transaction
                session.commit()
                
                action = "Created" if bill_created else "Updated"
                console.print(f"  [green]✓[/green] {action} bill: {bill.external_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to persist bill package: {e}")
            if session:
                session.rollback()
            return False
            
    def get_stats(self) -> dict:
        """Get storage statistics."""
        return self.stats
        
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "bills_created": 0,
            "bills_updated": 0,
            "explanations_created": 0,
            "explanations_updated": 0,
            "embeddings_created": 0
        }
