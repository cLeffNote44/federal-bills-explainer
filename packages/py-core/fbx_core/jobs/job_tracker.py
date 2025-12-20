"""Job tracking system for monitoring ingestion and other jobs."""

import uuid
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
import json
import traceback

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

logger = logging.getLogger(__name__)
console = Console()


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class JobConfig:
    """Configuration for a job."""
    job_type: str = "sync"
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    max_records: Optional[int] = None
    dry_run: bool = False
    triggered_by: str = "manual"
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobMetrics:
    """Metrics for a running job."""
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    skipped_records: int = 0
    api_calls_made: int = 0
    api_errors: int = 0
    start_time: Optional[datetime] = None
    
    def increment_processed(self):
        """Increment processed counter."""
        self.processed_records += 1
    
    def increment_failed(self):
        """Increment failed counter."""
        self.failed_records += 1
    
    def increment_skipped(self):
        """Increment skipped counter."""
        self.skipped_records += 1
    
    def increment_api_call(self):
        """Increment API call counter."""
        self.api_calls_made += 1
    
    def increment_api_error(self):
        """Increment API error counter."""
        self.api_errors += 1
    
    def get_duration_seconds(self) -> float:
        """Get duration in seconds."""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0
    
    def get_throughput(self) -> float:
        """Get processing throughput (records/second)."""
        duration = self.get_duration_seconds()
        if duration > 0:
            return self.processed_records / duration
        return 0
    
    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        total = self.processed_records + self.failed_records
        if total > 0:
            return (self.processed_records / total) * 100
        return 0


class JobTracker:
    """Track and monitor job execution."""
    
    def __init__(self, database_url: str):
        """Initialize job tracker."""
        self.database_url = database_url
        self.connection = None
        self.job_id = None
        self.metrics = JobMetrics()
        self.config = JobConfig()
    
    def connect(self):
        """Connect to database."""
        if not self.connection:
            self.connection = psycopg2.connect(self.database_url)
    
    def disconnect(self):
        """Disconnect from database."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def create_job(self, config: JobConfig) -> str:
        """Create a new job and return job ID."""
        self.connect()
        self.job_id = f"job_{uuid.uuid4().hex[:12]}_{int(time.time())}"
        self.config = config
        self.metrics = JobMetrics(start_time=datetime.now())
        
        with self.connection.cursor() as cur:
            cur.execute("""
                INSERT INTO ingestion_jobs (
                    job_id, job_type, status, from_date, to_date, 
                    max_records, dry_run, triggered_by, config
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.job_id,
                config.job_type,
                JobStatus.PENDING.value,
                config.from_date,
                config.to_date,
                config.max_records,
                config.dry_run,
                config.triggered_by,
                Json(config.config) if config.config else None
            ))
            self.connection.commit()
        
        logger.info(f"Created job {self.job_id}")
        return self.job_id
    
    def start_job(self):
        """Mark job as running."""
        if not self.job_id:
            raise ValueError("No job created")
        
        self.metrics.start_time = datetime.now()
        
        with self.connection.cursor() as cur:
            cur.execute("""
                UPDATE ingestion_jobs 
                SET status = %s, started_at = %s
                WHERE job_id = %s
            """, (JobStatus.RUNNING.value, datetime.now(), self.job_id))
            self.connection.commit()
        
        self.log(LogLevel.INFO, "Job started")
    
    def complete_job(self, notes: Optional[str] = None):
        """Mark job as completed."""
        if not self.job_id:
            raise ValueError("No job created")
        
        duration = self.metrics.get_duration_seconds()
        avg_time = (duration * 1000 / self.metrics.processed_records) if self.metrics.processed_records > 0 else 0
        
        with self.connection.cursor() as cur:
            cur.execute("""
                UPDATE ingestion_jobs 
                SET status = %s, completed_at = %s, duration_seconds = %s,
                    total_records = %s, processed_records = %s, failed_records = %s,
                    skipped_records = %s, api_calls_made = %s, api_errors = %s,
                    avg_record_time_ms = %s, notes = %s
                WHERE job_id = %s
            """, (
                JobStatus.COMPLETED.value,
                datetime.now(),
                duration,
                self.metrics.total_records,
                self.metrics.processed_records,
                self.metrics.failed_records,
                self.metrics.skipped_records,
                self.metrics.api_calls_made,
                self.metrics.api_errors,
                avg_time,
                notes,
                self.job_id
            ))
            self.connection.commit()
        
        self.log(LogLevel.INFO, f"Job completed successfully. Processed {self.metrics.processed_records} records.")
    
    def fail_job(self, error_message: str, error_details: Optional[Dict] = None):
        """Mark job as failed."""
        if not self.job_id:
            raise ValueError("No job created")
        
        duration = self.metrics.get_duration_seconds()
        
        with self.connection.cursor() as cur:
            cur.execute("""
                UPDATE ingestion_jobs 
                SET status = %s, completed_at = %s, duration_seconds = %s,
                    total_records = %s, processed_records = %s, failed_records = %s,
                    error_message = %s, error_details = %s, last_error_at = %s
                WHERE job_id = %s
            """, (
                JobStatus.FAILED.value,
                datetime.now(),
                duration,
                self.metrics.total_records,
                self.metrics.processed_records,
                self.metrics.failed_records,
                error_message,
                Json(error_details) if error_details else None,
                datetime.now(),
                self.job_id
            ))
            self.connection.commit()
        
        self.log(LogLevel.ERROR, f"Job failed: {error_message}", error_details)
    
    def update_metrics(self):
        """Update job metrics in database."""
        if not self.job_id:
            return
        
        with self.connection.cursor() as cur:
            cur.execute("""
                UPDATE ingestion_jobs 
                SET total_records = %s, processed_records = %s, 
                    failed_records = %s, skipped_records = %s,
                    api_calls_made = %s, api_errors = %s
                WHERE job_id = %s
            """, (
                self.metrics.total_records,
                self.metrics.processed_records,
                self.metrics.failed_records,
                self.metrics.skipped_records,
                self.metrics.api_calls_made,
                self.metrics.api_errors,
                self.job_id
            ))
            self.connection.commit()
    
    def log(self, level: LogLevel, message: str, details: Optional[Dict] = None, record_id: Optional[str] = None):
        """Add log entry for the job."""
        if not self.job_id:
            return
        
        with self.connection.cursor() as cur:
            cur.execute("""
                INSERT INTO job_logs (job_id, level, message, details, record_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                self.job_id,
                level.value,
                message,
                Json(details) if details else None,
                record_id
            ))
            self.connection.commit()
        
        # Also log to Python logger
        log_method = getattr(logger, level.value.lower(), logger.info)
        log_method(f"[{self.job_id}] {message}")
    
    def add_metric(self, metric_name: str, metric_value: float, unit: Optional[str] = None, tags: Optional[Dict] = None):
        """Add a metric data point."""
        if not self.job_id:
            return
        
        with self.connection.cursor() as cur:
            cur.execute("""
                INSERT INTO job_metrics (job_id, metric_name, metric_value, unit, tags)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                self.job_id,
                metric_name,
                metric_value,
                unit,
                Json(tags) if tags else None
            ))
            self.connection.commit()
    
    @contextmanager
    def track_job(self, config: JobConfig):
        """Context manager for tracking a job."""
        try:
            self.create_job(config)
            self.start_job()
            yield self
            self.complete_job()
        except Exception as e:
            error_details = {
                "traceback": traceback.format_exc(),
                "type": type(e).__name__
            }
            self.fail_job(str(e), error_details)
            raise
        finally:
            self.disconnect()
    
    def get_job_status(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of a job."""
        job_id = job_id or self.job_id
        if not job_id:
            raise ValueError("No job ID specified")
        
        self.connect()
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM ingestion_jobs WHERE job_id = %s", (job_id,))
            return cur.fetchone()
    
    def get_recent_jobs(self, limit: int = 10, job_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent jobs."""
        self.connect()
        
        query = "SELECT * FROM ingestion_jobs"
        params = []
        
        if job_type:
            query += " WHERE job_type = %s"
            params.append(job_type)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    
    def get_job_logs(self, job_id: Optional[str] = None, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get logs for a job."""
        job_id = job_id or self.job_id
        if not job_id:
            raise ValueError("No job ID specified")
        
        self.connect()
        query = "SELECT * FROM job_logs WHERE job_id = %s"
        params = [job_id]
        
        if level:
            query += " AND level = %s"
            params.append(level)
        
        query += " ORDER BY timestamp"
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    
    def get_job_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get job statistics for the last N days."""
        self.connect()
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            # Overall statistics
            cur.execute("""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
                    AVG(CASE WHEN status = 'completed' THEN duration_seconds END) as avg_duration,
                    SUM(CASE WHEN status = 'completed' THEN processed_records ELSE 0 END) as total_processed
                FROM ingestion_jobs
                WHERE created_at > CURRENT_DATE - INTERVAL '%s days'
            """, (days,))
            overall = cur.fetchone()
            
            # Daily breakdown
            cur.execute("""
                SELECT * FROM v_job_statistics
                WHERE date > CURRENT_DATE - INTERVAL '%s days'
                ORDER BY date DESC
            """, (days,))
            daily = cur.fetchall()
            
            return {
                "overall": overall,
                "daily": daily
            }
    
    def display_progress(self):
        """Display live progress of the current job."""
        if not self.job_id:
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Job {self.job_id}",
                total=self.metrics.total_records or 100
            )
            
            while self.metrics.processed_records < self.metrics.total_records:
                progress.update(
                    task, 
                    completed=self.metrics.processed_records,
                    description=f"[cyan]Processing... ({self.metrics.processed_records}/{self.metrics.total_records})"
                )
                time.sleep(0.1)  # Update frequency


class JobMonitor:
    """Monitor and display job statistics."""
    
    def __init__(self, database_url: str):
        """Initialize job monitor."""
        self.database_url = database_url
        self.tracker = JobTracker(database_url)
    
    def display_recent_jobs(self, limit: int = 10):
        """Display recent jobs in a table."""
        jobs = self.tracker.get_recent_jobs(limit)
        
        if not jobs:
            console.print("[yellow]No jobs found[/yellow]")
            return
        
        table = Table(title=f"Recent Jobs (Last {limit})", show_header=True)
        table.add_column("Job ID", style="cyan")
        table.add_column("Type", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Started", style="yellow")
        table.add_column("Duration", style="magenta")
        table.add_column("Processed", style="green")
        table.add_column("Failed", style="red")
        
        for job in jobs:
            status_color = {
                "completed": "green",
                "failed": "red",
                "running": "yellow",
                "cancelled": "dim"
            }.get(job['status'], "white")
            
            duration = f"{job['duration_seconds']:.1f}s" if job['duration_seconds'] else "N/A"
            
            table.add_row(
                job['job_id'][:20],
                job['job_type'],
                f"[{status_color}]{job['status']}[/{status_color}]",
                job['started_at'].strftime("%Y-%m-%d %H:%M") if job['started_at'] else "Not started",
                duration,
                str(job['processed_records']),
                str(job['failed_records'])
            )
        
        console.print(table)
    
    def display_statistics(self, days: int = 7):
        """Display job statistics."""
        stats = self.tracker.get_job_statistics(days)
        
        # Overall stats panel
        overall = stats['overall']
        panel_content = f"""
[bold]Jobs Summary (Last {days} Days)[/bold]

Total Jobs: [cyan]{overall['total_jobs']}[/cyan]
Completed: [green]{overall['completed']}[/green]
Failed: [red]{overall['failed']}[/red]
Running: [yellow]{overall['running']}[/yellow]

Average Duration: [magenta]{overall['avg_duration']:.1f}s[/magenta] if overall['avg_duration'] else 'N/A'
Total Records Processed: [blue]{overall['total_processed']:,}[/blue]
Success Rate: [green]{(overall['completed'] / overall['total_jobs'] * 100):.1f}%[/green] if overall['total_jobs'] > 0 else 'N/A'
"""
        
        console.print(Panel(panel_content, title="Job Statistics"))
        
        # Daily breakdown table
        if stats['daily']:
            table = Table(title="Daily Breakdown", show_header=True)
            table.add_column("Date", style="cyan")
            table.add_column("Total", style="white")
            table.add_column("Completed", style="green")
            table.add_column("Failed", style="red")
            table.add_column("Avg Duration", style="magenta")
            table.add_column("Throughput", style="blue")
            
            for day in stats['daily']:
                table.add_row(
                    str(day['date']),
                    str(day['total_jobs']),
                    str(day['completed_jobs']),
                    str(day['failed_jobs']),
                    f"{day['avg_duration']:.1f}s" if day['avg_duration'] else "N/A",
                    f"{day['avg_throughput']:.1f}/s" if day['avg_throughput'] else "N/A"
                )
            
            console.print(table)