"""Incremental sync management for efficient data updates."""

import hashlib
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

import psycopg2
from psycopg2.extras import RealDictCursor, Json

logger = logging.getLogger(__name__)


@dataclass
class SyncState:
    """State of the last successful sync."""
    sync_type: str
    last_sync_at: Optional[datetime] = None
    last_successful_job_id: Optional[str] = None
    last_bill_date: Optional[datetime] = None
    last_bill_id: Optional[str] = None
    total_synced: int = 0
    metadata: Dict[str, Any] = None


class IncrementalSyncManager:
    """Manage incremental/delta synchronization."""
    
    def __init__(self, database_url: str):
        """Initialize sync manager."""
        self.database_url = database_url
        self.connection = None
    
    def connect(self):
        """Connect to database."""
        if not self.connection:
            self.connection = psycopg2.connect(self.database_url)
    
    def disconnect(self):
        """Disconnect from database."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_sync_state(self, sync_type: str = "bills") -> Optional[SyncState]:
        """Get the last sync state."""
        self.connect()
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM sync_state WHERE sync_type = %s",
                (sync_type,)
            )
            row = cur.fetchone()
            
            if row:
                return SyncState(
                    sync_type=row['sync_type'],
                    last_sync_at=row['last_sync_at'],
                    last_successful_job_id=row['last_successful_job_id'],
                    last_bill_date=row['last_bill_date'],
                    last_bill_id=row['last_bill_id'],
                    total_synced=row['total_synced'],
                    metadata=row['metadata']
                )
            return None
    
    def update_sync_state(
        self,
        sync_type: str,
        job_id: str,
        last_bill_date: Optional[datetime] = None,
        last_bill_id: Optional[str] = None,
        records_synced: int = 0,
        metadata: Optional[Dict] = None
    ):
        """Update the sync state after successful sync."""
        self.connect()
        
        with self.connection.cursor() as cur:
            # Check if state exists
            cur.execute(
                "SELECT id FROM sync_state WHERE sync_type = %s",
                (sync_type,)
            )
            exists = cur.fetchone()
            
            if exists:
                # Update existing
                cur.execute("""
                    UPDATE sync_state 
                    SET last_sync_at = %s,
                        last_successful_job_id = %s,
                        last_bill_date = %s,
                        last_bill_id = %s,
                        total_synced = total_synced + %s,
                        metadata = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE sync_type = %s
                """, (
                    datetime.now(),
                    job_id,
                    last_bill_date,
                    last_bill_id,
                    records_synced,
                    Json(metadata) if metadata else None,
                    sync_type
                ))
            else:
                # Insert new
                cur.execute("""
                    INSERT INTO sync_state (
                        sync_type, last_sync_at, last_successful_job_id,
                        last_bill_date, last_bill_id, total_synced, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    sync_type,
                    datetime.now(),
                    job_id,
                    last_bill_date,
                    last_bill_id,
                    records_synced,
                    Json(metadata) if metadata else None
                ))
            
            self.connection.commit()
            logger.info(f"Updated sync state for {sync_type}: {records_synced} records")
    
    def get_incremental_date_range(
        self,
        sync_type: str = "bills",
        lookback_days: int = 1
    ) -> Tuple[datetime, datetime]:
        """
        Get date range for incremental sync.
        
        Returns:
            Tuple of (from_date, to_date)
        """
        state = self.get_sync_state(sync_type)
        
        # Default to last N days if no previous sync
        if not state or not state.last_sync_at:
            from_date = datetime.now() - timedelta(days=lookback_days)
        else:
            # Start from last sync time with small overlap
            from_date = state.last_sync_at - timedelta(hours=1)
        
        to_date = datetime.now()
        
        logger.info(f"Incremental sync range: {from_date} to {to_date}")
        return from_date, to_date
    
    def calculate_checksum(self, bill_data: Dict[str, Any]) -> str:
        """Calculate checksum for bill data to detect changes."""
        # Select fields that indicate meaningful changes
        checksum_fields = {
            'title': bill_data.get('title', ''),
            'summary': bill_data.get('summary', ''),
            'latest_action_text': bill_data.get('latest_action_text', ''),
            'law_number': bill_data.get('law_number', ''),
            'sponsor': bill_data.get('sponsor', ''),
        }
        
        # Create stable JSON representation
        json_str = json.dumps(checksum_fields, sort_keys=True)
        
        # Calculate SHA256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def detect_bill_changes(self, bill_id: int, new_checksum: str) -> bool:
        """
        Detect if a bill has changed.
        
        Returns:
            True if bill has changed, False otherwise
        """
        self.connect()
        
        with self.connection.cursor() as cur:
            cur.execute(
                "SELECT checksum FROM bills WHERE id = %s",
                (bill_id,)
            )
            result = cur.fetchone()
            
            if result and result[0]:
                return result[0] != new_checksum
            
            return True  # Consider new if no checksum
    
    def save_bill_version(
        self,
        bill_id: int,
        bill_data: Dict[str, Any],
        change_type: str,
        change_description: Optional[str] = None
    ):
        """Save a version of the bill for history tracking."""
        self.connect()
        
        with self.connection.cursor() as cur:
            # Get current version
            cur.execute(
                "SELECT version FROM bills WHERE id = %s",
                (bill_id,)
            )
            current_version = cur.fetchone()[0] or 1
            
            # Insert version record
            cur.execute("""
                INSERT INTO bill_versions (
                    bill_id, version, external_id, title, summary,
                    latest_action_text, change_type, change_description,
                    checksum
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                bill_id,
                current_version,
                bill_data.get('external_id'),
                bill_data.get('title'),
                bill_data.get('summary'),
                bill_data.get('latest_action_text'),
                change_type,
                change_description,
                self.calculate_checksum(bill_data)
            ))
            
            # Update bill version
            cur.execute("""
                UPDATE bills 
                SET version = version + 1,
                    last_modified = CURRENT_TIMESTAMP,
                    checksum = %s
                WHERE id = %s
            """, (
                self.calculate_checksum(bill_data),
                bill_id
            ))
            
            self.connection.commit()
            logger.info(f"Saved version {current_version} for bill {bill_id}")
    
    def get_bills_needing_update(
        self,
        since_date: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get bills that need updating based on date."""
        self.connect()
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, external_id, checksum, version, last_modified
                FROM bills
                WHERE last_modified IS NULL 
                   OR last_modified < %s
                ORDER BY last_modified ASC NULLS FIRST
                LIMIT %s
            """, (since_date, limit))
            
            return cur.fetchall()
    
    def mark_unchanged_bills(self, bill_ids: List[int]):
        """Mark bills as checked but unchanged."""
        if not bill_ids:
            return
        
        self.connect()
        
        with self.connection.cursor() as cur:
            cur.execute("""
                UPDATE bills
                SET last_modified = CURRENT_TIMESTAMP
                WHERE id = ANY(%s)
            """, (bill_ids,))
            
            self.connection.commit()
            logger.info(f"Marked {len(bill_ids)} bills as unchanged")
    
    def get_change_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of recent changes."""
        self.connect()
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            # Count changes by type
            cur.execute("""
                SELECT 
                    change_type,
                    COUNT(*) as count,
                    COUNT(DISTINCT bill_id) as unique_bills
                FROM bill_versions
                WHERE created_at > CURRENT_DATE - INTERVAL '%s days'
                GROUP BY change_type
            """, (days,))
            
            changes_by_type = cur.fetchall()
            
            # Count total changes
            cur.execute("""
                SELECT 
                    COUNT(*) as total_changes,
                    COUNT(DISTINCT bill_id) as bills_changed
                FROM bill_versions
                WHERE created_at > CURRENT_DATE - INTERVAL '%s days'
            """, (days,))
            
            totals = cur.fetchone()
            
            # Get recent sync states
            cur.execute("""
                SELECT sync_type, last_sync_at, total_synced
                FROM sync_state
                ORDER BY last_sync_at DESC
            """)
            
            sync_states = cur.fetchall()
            
            return {
                'period_days': days,
                'total_changes': totals['total_changes'],
                'bills_changed': totals['bills_changed'],
                'changes_by_type': changes_by_type,
                'sync_states': sync_states
            }


class IncrementalSyncStrategy:
    """Strategy for incremental synchronization."""
    
    def __init__(self, sync_manager: IncrementalSyncManager):
        """Initialize strategy."""
        self.sync_manager = sync_manager
    
    def should_full_sync(self, sync_type: str = "bills") -> bool:
        """Determine if full sync is needed."""
        state = self.sync_manager.get_sync_state(sync_type)
        
        # Full sync if never synced
        if not state or not state.last_sync_at:
            return True
        
        # Full sync if last sync was too long ago (>30 days)
        days_since = (datetime.now() - state.last_sync_at).days
        if days_since > 30:
            logger.info(f"Full sync recommended: {days_since} days since last sync")
            return True
        
        return False
    
    def get_sync_params(
        self,
        sync_type: str = "bills",
        force_full: bool = False
    ) -> Dict[str, Any]:
        """Get parameters for sync operation."""
        if force_full or self.should_full_sync(sync_type):
            # Full sync parameters
            return {
                'mode': 'full',
                'from_date': (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                'to_date': datetime.now().strftime("%Y-%m-%d"),
                'max_records': None
            }
        else:
            # Incremental sync parameters
            from_date, to_date = self.sync_manager.get_incremental_date_range(sync_type)
            
            return {
                'mode': 'incremental',
                'from_date': from_date.strftime("%Y-%m-%d"),
                'to_date': to_date.strftime("%Y-%m-%d"),
                'max_records': 500  # Limit for incremental
            }
    
    def calculate_sync_efficiency(self, sync_type: str = "bills") -> Dict[str, Any]:
        """Calculate efficiency metrics for sync operations."""
        state = self.sync_manager.get_sync_state(sync_type)
        
        if not state:
            return {'efficiency': 'N/A', 'message': 'No sync history'}
        
        # Calculate metrics
        days_since = (datetime.now() - state.last_sync_at).days if state.last_sync_at else 0
        avg_per_day = state.total_synced / max(days_since, 1) if days_since > 0 else 0
        
        return {
            'total_synced': state.total_synced,
            'days_since_last': days_since,
            'avg_per_day': round(avg_per_day, 2),
            'last_job_id': state.last_successful_job_id,
            'efficiency': 'HIGH' if days_since < 2 else 'MEDIUM' if days_since < 7 else 'LOW'
        }