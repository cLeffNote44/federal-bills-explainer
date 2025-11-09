from typing import Optional, List
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from fbx_core.models.tables import Bill, Explanation, Embedding, IngestionState
from fbx_core.providers.base import AbstractProvider, BillRecord
from fbx_core.utils.settings import Settings
from fbx_core.services.embeddings import compute_text_and_hash, embed_text


class IngestionService:
    def __init__(self, provider: AbstractProvider, session: Session):
        self.provider = provider
        self.session = session
        self.settings = Settings()

    def run(self) -> int:
        logger.info(f"Starting ingestion with provider={self.provider.name}")
        
        # Get last run timestamp
        state = self.session.get(IngestionState, 1)
        since = None
        if state and state.last_run_at:
            since = state.last_run_at
        
        # Override with settings if configured
        if self.settings.ingest_since:
            since_dt = datetime.combine(self.settings.ingest_since, datetime.min.time(), tzinfo=timezone.utc)
            since = since_dt
            logger.info(f"Using ingest_since override: {since}")

        count = 0
        limit = self.settings.ingest_limit
        
        for rec in self.provider.fetch_bills_updated_since(since):
            if limit and count >= limit:
                logger.info(f"Reached ingestion limit of {limit} bills")
                break
                
            bill = self._upsert_bill(rec)
            if bill:
                if self.settings.explanations_enabled:
                    self._generate_explanation(bill)
                if self.settings.embeddings_enabled:
                    self._generate_embedding(bill)
                count += 1

        # Update watermark
        if not state:
            state = IngestionState(id=1)
            self.session.add(state)
        state.last_run_at = datetime.now(timezone.utc)
        self.session.commit()
        
        logger.info(f"Ingestion complete, processed {count} bills")
        return count

    def _upsert_bill(self, rec: BillRecord) -> Optional[Bill]:
        try:
            congress = rec.get("congress")
            bill_type = rec.get("bill_type")
            number = rec.get("number")
            
            if not all([congress, bill_type, number]):
                logger.warning(f"Missing required fields: {rec}")
                return None

            stmt = select(Bill).where(
                (Bill.congress == congress) &
                (Bill.bill_type == bill_type) &
                (Bill.number == number)
            )
            bill = self.session.scalars(stmt).first()
            
            if not bill:
                bill = Bill(congress=congress, bill_type=bill_type, number=number)
                self.session.add(bill)

            # Update fields
            bill.title = rec.get("title") or ""
            bill.summary = rec.get("summary") or ""
            bill.status = rec.get("status")
            bill.introduced_date = rec.get("introduced_date")
            bill.latest_action_date = rec.get("latest_action_date")
            bill.congress_url = rec.get("congress_url")
            bill.public_law_number = rec.get("public_law_number")
            bill.sponsor = rec.get("sponsor")
            bill.committees = rec.get("committees")
            bill.subjects = rec.get("subjects")
            bill.cosponsors_count = rec.get("cosponsors_count") or 0

            self.session.commit()
            logger.info(f"Upserted bill: {bill_type}-{number} (Congress {congress})")
            return bill
            
        except Exception as e:
            logger.error(f"Failed to upsert bill: {e}")
            self.session.rollback()
            return None

    def _generate_explanation(self, bill: Bill):
        try:
            # Check if already has explanation
            if bill.explanations:
                latest = max(bill.explanations, key=lambda e: e.version)
                if latest.model_name == self.settings.explain_model:
                    logger.debug(f"Bill {bill.id} already has explanation")
                    return
            
            # Generate new explanation (stub for now)
            text = f"This bill ({bill.bill_type.upper()}-{bill.number}) titled '{bill.title}' aims to..."
            if bill.summary:
                text += f"\n\nSummary: {bill.summary[:200]}..."
            
            exp = Explanation(
                bill_id=bill.id,
                model_name=self.settings.explain_model,
                text=text,
                version=len(bill.explanations) + 1 if bill.explanations else 1
            )
            self.session.add(exp)
            self.session.commit()
            logger.info(f"Generated explanation for bill {bill.id}")
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            self.session.rollback()

    def _generate_embedding(self, bill: Bill):
        try:
            # Get latest explanation if exists
            explanation_text = ""
            if bill.explanations:
                latest = max(bill.explanations, key=lambda e: e.version)
                explanation_text = latest.text
            
            # Compute hash
            combined_text, content_hash = compute_text_and_hash(
                bill.title, bill.summary or "", explanation_text, self.settings.embedding_model
            )
            
            # Check if embedding exists
            stmt = select(Embedding).where(
                (Embedding.content_hash == content_hash) &
                (Embedding.model_name == self.settings.embedding_model)
            )
            existing = self.session.scalars(stmt).first()
            if existing:
                logger.debug(f"Embedding already exists for bill {bill.id}")
                return
            
            # Generate embedding
            vector = embed_text(combined_text, self.settings.embedding_model)
            
            emb = Embedding(
                bill_id=bill.id,
                content_kind="document",
                model_name=self.settings.embedding_model,
                content_hash=content_hash,
                vector=vector
            )
            self.session.add(emb)
            self.session.commit()
            logger.info(f"Generated embedding for bill {bill.id}")
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            self.session.rollback()
