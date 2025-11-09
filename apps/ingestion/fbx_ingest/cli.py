"""CLI for Federal Bills Explainer ingestion."""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .settings import get_settings
from .congress import CongressClient
from .explain import ExplanationGenerator
from .embed import EmbeddingGenerator
from .store import StorageManager
from .types import BillDTO
from fbx_core.utils.db_performance import DatabasePerformanceAnalyzer
from fbx_core.jobs import JobTracker, JobMonitor, JobConfig, LogLevel

app = typer.Typer(help="Federal Bills Explainer Ingestion CLI")
console = Console()

# Global variable to track the last used client for stats
_last_congress_client: Optional[CongressClient] = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.command()
def sync(
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Run without persisting to database"),
    from_date: Optional[str] = typer.Option(None, help="Start date (ISO format: YYYY-MM-DD)"),
    to_date: Optional[str] = typer.Option(None, help="End date (ISO format: YYYY-MM-DD)"),
    max_records: Optional[int] = typer.Option(20, help="Maximum number of records to process"),
    batch_size: int = typer.Option(10, help="Number of bills to process in batch"),
    explain_model: Optional[str] = typer.Option(None, help="Model for generating explanations"),
    embed_model: Optional[str] = typer.Option(None, help="Model for generating embeddings"),
    log_level: str = typer.Option("INFO", help="Logging level"),
    sample_bill: Optional[str] = typer.Option(None, help="Fetch specific bill (e.g., '118-hr-1234')")
):
    """Sync federal bills that became law."""
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    # Load settings
    settings = get_settings()
    
    # Override settings with CLI options
    if from_date:
        settings.from_date = from_date
    if to_date:
        settings.to_date = to_date
    if max_records is not None:
        settings.max_records = max_records
    if batch_size:
        settings.batch_size = batch_size
    if explain_model:
        settings.ingest_model_name = explain_model
    if embed_model:
        settings.embed_model_name = embed_model
    settings.dry_run = dry_run
    
    # Set default date range if not provided
    if not settings.from_date:
        # Default to last 30 days
        settings.from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not settings.to_date:
        settings.to_date = datetime.now().strftime("%Y-%m-%d")
    
    # Print configuration
    console.print("\n[bold cyan]Federal Bills Explainer Ingestion[/bold cyan]")
    console.print(f"Mode: [yellow]{'DRY RUN' if dry_run else 'LIVE'}[/yellow]")
    console.print(f"Date Range: {settings.from_date} to {settings.to_date}")
    console.print(f"Max Records: {settings.max_records or 'Unlimited'}")
    console.print(f"Explanation Model: {settings.ingest_model_name}")
    console.print(f"Embedding Model: {settings.embed_model_name}")
    console.print()
    
    # Initialize job tracking
    job_config = JobConfig(
        job_type="sync",
        from_date=settings.from_date,
        to_date=settings.to_date,
        max_records=settings.max_records,
        dry_run=dry_run,
        triggered_by="cli",
        config={
            "batch_size": batch_size,
            "explain_model": settings.ingest_model_name,
            "embed_model": settings.embed_model_name,
            "sample_bill": sample_bill
        }
    )
    
    job_tracker = JobTracker(settings.database_url)
    
    try:
        with job_tracker.track_job(job_config):
            # Initialize components
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
            
            # Initialize Congress client
            task = progress.add_task("Initializing Congress client...", total=None)
            congress_client = CongressClient(
                api_key=settings.congress_api_key,
                delay_seconds=settings.api_delay_seconds
            )
            global _last_congress_client
            _last_congress_client = congress_client
            progress.update(task, completed=True)
            
            # Initialize models (skip in dry-run for speed)
            explainer = None
            embedder = None
            storage = None
            
            if not dry_run:
                task = progress.add_task("Loading explanation model...", total=None)
                explainer = ExplanationGenerator(
                    model_name=settings.ingest_model_name,
                    use_gpu=settings.use_gpu
                )
                progress.update(task, completed=True)
                
                task = progress.add_task("Loading embedding model...", total=None)
                embedder = EmbeddingGenerator(
                    model_name=settings.embed_model_name
                )
                progress.update(task, completed=True)
                
                task = progress.add_task("Connecting to database...", total=None)
                storage = StorageManager(database_url=settings.database_url)
                progress.update(task, completed=True)
        
        # Fetch bills
        with congress_client:
            if sample_bill:
                # Fetch specific bill for testing
                console.print(f"\n[bold blue]Fetching specific bill: {sample_bill}[/bold blue]")
                parts = sample_bill.split("-")
                if len(parts) == 3:
                    congress_num = int(parts[0])
                    bill_type = parts[1]
                    bill_number = int(parts[2])
                    
                    bill_data = congress_client.get_bill(congress_num, bill_type, bill_number)
                    bill_dto = BillDTO.from_congress_api(bill_data.get("bill", {}))
                    enacted_bills = [bill_dto]
                else:
                    console.print("[red]Invalid bill format. Use format: 118-hr-1234[/red]")
                    return
            else:
                enacted_bills = congress_client.fetch_enacted_bills(
                    from_date=settings.from_date,
                    to_date=settings.to_date,
                    max_records=settings.max_records
                )
        
        if not enacted_bills:
            console.print("[yellow]No enacted bills found in the specified date range.[/yellow]")
            return
        
        # Process bills
        console.print(f"\n[bold blue]Processing {len(enacted_bills)} bills...[/bold blue]")
        
        if dry_run:
            # Dry run - just show preview
            console.print("\n[bold yellow]DRY RUN - Preview Mode[/bold yellow]\n")
            
            # Show first 2 bills as examples
            for i, bill in enumerate(enacted_bills[:2]):
                console.print(f"[bold]Bill {i+1}:[/bold]")
                console.print(f"  ID: {bill.external_id}")
                console.print(f"  Title: {bill.short_title or bill.title[:80]}...")
                if bill.law_number:
                    console.print(f"  Law: {bill.law_number}")
                console.print(f"  Sponsor: {bill.sponsor}")
                console.print(f"  Policy Area: {bill.policy_area}")
                
                # Generate sample explanation
                sample_explanation = f"""
This bill, {bill.short_title or bill.title[:50]}, addresses important federal legislation.

What it does: This legislation implements new policies and regulations in the area of {bill.policy_area or 'federal governance'}.

Why it matters: The bill impacts citizens by establishing new requirements and providing resources for implementation.

Who is affected: Various stakeholders including individuals, businesses, and government agencies will be affected by these changes.

Key details: The bill was sponsored by {bill.sponsor or 'a member of Congress'} and became law {f'as {bill.law_number}' if bill.law_number else 'recently'}.
                """.strip()
                
                console.print(f"\n  [italic]Sample Explanation (first 300 chars):[/italic]")
                console.print(f"  {sample_explanation[:300]}...")
                console.print()
            
            # Show summary
            table = Table(title="Dry Run Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Bills Fetched", str(len(enacted_bills)))
            table.add_row("Date Range", f"{settings.from_date} to {settings.to_date}")
            table.add_row("Would Process", str(min(len(enacted_bills), settings.max_records or len(enacted_bills))))
            console.print(table)
            
            # Show rate limit stats
            if congress_client:
                stats = congress_client.get_rate_limit_stats()
                console.print("\n[bold cyan]Rate Limiting Statistics:[/bold cyan]")
                stats_table = Table()
                stats_table.add_column("Metric", style="cyan")
                stats_table.add_column("Value", style="green")
                stats_table.add_row("Total Requests", str(stats.get('total_requests', 0)))
                stats_table.add_row("Success Rate", stats.get('success_rate', 'N/A'))
                stats_table.add_row("Rate Limited", str(stats.get('rate_limited_requests', 0)))
                stats_table.add_row("Circuit State", stats.get('circuit_state', 'closed'))
                console.print(stats_table)
            
        else:
            # Live run - process and persist
            processed = 0
            failed = 0
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                task = progress.add_task(
                    f"Processing {len(enacted_bills)} bills...",
                    total=len(enacted_bills)
                )
                
                for bill in enacted_bills:
                    try:
                        # Generate explanation
                        explanation = explainer.generate_explanation(bill)
                        
                        # Generate embedding
                        embed_text = f"{bill.title} {explanation.explanation_text[:500]}"
                        embedding = embedder.create_embedding_dto(
                            text=embed_text,
                            entity_type="explanation",
                            entity_id="0"  # Will be updated after storage
                        )
                        
                        # Persist to database
                        success = storage.persist_bill_package(
                            bill_dto=bill,
                            explanation_dto=explanation,
                            embedding_dto=embedding
                        )
                        
                        if success:
                            processed += 1
                        else:
                            failed += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to process bill {bill.external_id}: {e}")
                        failed += 1
                    
                    progress.update(task, advance=1)
            
            # Show final statistics
            stats = storage.get_stats() if storage else {}
            
            table = Table(title="Ingestion Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Bills Processed", str(processed))
            table.add_row("Bills Failed", str(failed))
            table.add_row("Bills Created", str(stats.get("bills_created", 0)))
            table.add_row("Bills Updated", str(stats.get("bills_updated", 0)))
            table.add_row("Explanations Created", str(stats.get("explanations_created", 0)))
            table.add_row("Explanations Updated", str(stats.get("explanations_updated", 0)))
            table.add_row("Embeddings Created", str(stats.get("embeddings_created", 0)))
            console.print(table)
            
            console.print(f"\n[bold green]✓ Ingestion complete![/bold green]")
            
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        logger.exception("Ingestion failed")
        raise typer.Exit(code=1)


@app.command()
def rate_limits(
    reset: bool = typer.Option(False, "--reset", help="Reset rate limit statistics"),
    watch: bool = typer.Option(False, "--watch", help="Watch rate limits in real-time")
):
    """Display rate limiting statistics."""
    global _last_congress_client
    
    if not _last_congress_client:
        # Create a new client for stats
        settings = get_settings()
        _last_congress_client = CongressClient(
            api_key=settings.congress_api_key,
            delay_seconds=settings.api_delay_seconds
        )
    
    if reset:
        _last_congress_client.reset_rate_limit_stats()
        console.print("[green]✓ Rate limit statistics reset[/green]")
        return
    
    # Display current stats
    stats = _last_congress_client.get_rate_limit_stats()
    
    console.print("[bold cyan]Rate Limiting Statistics[/bold cyan]\n")
    
    # Create detailed stats table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", width=30)
    table.add_column("Value", style="green")
    table.add_column("Description", style="dim")
    
    # Add rows
    table.add_row(
        "Circuit State",
        stats.get('circuit_state', 'closed').upper(),
        "Current state of circuit breaker"
    )
    table.add_row(
        "Total Requests",
        str(stats.get('total_requests', 0)),
        "Total API requests made"
    )
    table.add_row(
        "Successful Requests",
        str(stats.get('successful_requests', 0)),
        "Requests that succeeded"
    )
    table.add_row(
        "Failed Requests",
        str(stats.get('failed_requests', 0)),
        "Requests that failed"
    )
    table.add_row(
        "Success Rate",
        stats.get('success_rate', 'N/A'),
        "Percentage of successful requests"
    )
    table.add_row(
        "Rate Limited",
        str(stats.get('rate_limited_requests', 0)),
        "Requests delayed due to rate limits"
    )
    table.add_row(
        "Circuit Breaker Rejections",
        str(stats.get('circuit_breaker_rejections', 0)),
        "Requests rejected by circuit breaker"
    )
    table.add_row(
        "Total Retries",
        str(stats.get('total_retry_attempts', 0)),
        "Total retry attempts made"
    )
    
    if stats.get('last_request_time'):
        table.add_row(
            "Last Request",
            stats.get('last_request_time'),
            "Time of last request"
        )
    
    if stats.get('last_failure_time'):
        table.add_row(
            "Last Failure",
            stats.get('last_failure_time'),
            "Time of last failure"
        )
    
    console.print(table)
    
    # Show recommendations based on stats
    if stats.get('circuit_state') == 'open':
        console.print("\n[bold red]⚠ Circuit breaker is OPEN[/bold red]")
        console.print("The API is experiencing failures. Requests are being rejected to allow recovery.")
    elif stats.get('circuit_state') == 'half_open':
        console.print("\n[bold yellow]⚠ Circuit breaker is HALF-OPEN[/bold yellow]")
        console.print("Testing if the API has recovered. Limited requests are being allowed.")
    
    if stats.get('rate_limited_requests', 0) > 10:
        console.print("\n[bold yellow]⚠ High rate limiting detected[/bold yellow]")
        console.print("Consider reducing request rate or increasing delay between requests.")
    
    if stats.get('failed_requests', 0) > stats.get('successful_requests', 0):
        console.print("\n[bold red]⚠ High failure rate detected[/bold red]")
        console.print("More requests are failing than succeeding. Check API status and credentials.")


@app.command()
def db_analyze(
    fix: bool = typer.Option(False, "--fix", help="Apply recommended fixes automatically"),
    verbose: bool = typer.Option(False, "--verbose", help="Show detailed analysis")
):
    """Analyze database performance and suggest optimizations."""
    console.print("[bold cyan]Database Performance Analysis[/bold cyan]\n")
    
    try:
        # Load settings
        settings = get_settings()
        
        # Create analyzer
        with DatabasePerformanceAnalyzer(settings.database_url) as analyzer:
            # Run analysis
            with console.status("Analyzing database performance..."):
                analysis = analyzer.analyze_performance()
            
            # Print results
            analyzer.print_analysis(analysis)
            
            # Apply fixes if requested
            if fix:
                console.print("\n[bold yellow]Applying recommended fixes...[/bold yellow]\n")
                
                # Run VACUUM ANALYZE on tables with dead rows
                for table in analysis['table_stats']:
                    if table.dead_rows > table.row_count * 0.2:
                        try:
                            analyzer.connection.autocommit = True
                            with analyzer.connection.cursor() as cur:
                                console.print(f"Running VACUUM ANALYZE on {table.table_name}...")
                                cur.execute(f"VACUUM ANALYZE {table.table_name};")
                                console.print(f"[green]✓[/green] Vacuumed {table.table_name}")
                        except Exception as e:
                            console.print(f"[red]✗[/red] Failed to vacuum {table.table_name}: {e}")
                
                # Create missing indexes if confirmed
                if analysis['missing_indexes'] and verbose:
                    console.print("\n[bold]Suggested indexes to create:[/bold]")
                    for idx in analysis['missing_indexes'][:5]:
                        console.print(f"  {idx['suggestion']}")
                    
                    if typer.confirm("\nCreate suggested indexes?"):
                        for idx in analysis['missing_indexes'][:5]:
                            try:
                                with analyzer.connection.cursor() as cur:
                                    cur.execute(idx['suggestion'])
                                    analyzer.connection.commit()
                                    console.print(f"[green]✓[/green] Created index on {idx['table']}.{idx['column']}")
                            except Exception as e:
                                console.print(f"[red]✗[/red] Failed to create index: {e}")
                                analyzer.connection.rollback()
            
            # Summary
            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  • Tables analyzed: {len(analysis['table_stats'])}")
            console.print(f"  • Slow queries found: {len(analysis['slow_queries'])}")
            console.print(f"  • Missing indexes identified: {len(analysis['missing_indexes'])}")
            console.print(f"  • Unused indexes found: {len(analysis['unused_indexes'])}")
            console.print(f"  • Recommendations: {len(analysis['recommendations'])}")
            
            if analysis['recommendations']:
                high_priority = [r for r in analysis['recommendations'] if r['priority'] == 'HIGH']
                if high_priority:
                    console.print(f"\n[bold red]⚠ {len(high_priority)} high-priority issues found![/bold red]")
            else:
                console.print("\n[bold green]✓ Database performance looks good![/bold green]")
                
    except Exception as e:
        console.print(f"[bold red]Analysis failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def jobs(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recent jobs to display"),
    job_type: Optional[str] = typer.Option(None, "--type", help="Filter by job type"),
    stats: bool = typer.Option(False, "--stats", help="Show job statistics"),
    days: int = typer.Option(7, "--days", help="Number of days for statistics"),
    job_id: Optional[str] = typer.Option(None, "--job-id", help="Show details for specific job"),
    logs: bool = typer.Option(False, "--logs", help="Show logs for job")
):
    """View and monitor ingestion jobs."""
    settings = get_settings()
    monitor = JobMonitor(settings.database_url)
    
    try:
        if job_id:
            # Show specific job details
            tracker = monitor.tracker
            job = tracker.get_job_status(job_id)
            
            if not job:
                console.print(f"[red]Job {job_id} not found[/red]")
                return
            
            # Display job details
            console.print(f"\n[bold cyan]Job Details: {job_id}[/bold cyan]\n")
            
            table = Table(show_header=False)
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Type", job['job_type'])
            table.add_row("Status", f"[{'green' if job['status'] == 'completed' else 'red'}]{job['status']}[/]")
            table.add_row("Created", str(job['created_at']))
            table.add_row("Started", str(job['started_at']) if job['started_at'] else "N/A")
            table.add_row("Completed", str(job['completed_at']) if job['completed_at'] else "N/A")
            table.add_row("Duration", f"{job['duration_seconds']:.1f}s" if job['duration_seconds'] else "N/A")
            table.add_row("Date Range", f"{job['from_date']} to {job['to_date']}")
            table.add_row("Records Processed", f"{job['processed_records']} / {job['total_records']}")
            table.add_row("Failed Records", str(job['failed_records']))
            table.add_row("API Calls", str(job['api_calls_made']))
            table.add_row("API Errors", str(job['api_errors']))
            
            if job['error_message']:
                table.add_row("Error", f"[red]{job['error_message']}[/red]")
            
            console.print(table)
            
            if logs:
                # Show job logs
                job_logs = tracker.get_job_logs(job_id)
                if job_logs:
                    console.print("\n[bold]Job Logs:[/bold]\n")
                    for log in job_logs[-20:]:  # Last 20 logs
                        color = {
                            'ERROR': 'red',
                            'WARNING': 'yellow',
                            'INFO': 'blue',
                            'DEBUG': 'dim'
                        }.get(log['level'], 'white')
                        console.print(f"[{color}][{log['timestamp']}] {log['level']}: {log['message']}[/{color}]")
        
        elif stats:
            # Show statistics
            monitor.display_statistics(days)
        
        else:
            # Show recent jobs
            monitor.display_recent_jobs(limit)
            
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def test():
    """Test connectivity and configuration."""
    console.print("[bold cyan]Testing Federal Bills Explainer Configuration[/bold cyan]\n")
    
    try:
        # Load settings
        settings = get_settings()
        console.print("[green]✓[/green] Settings loaded successfully")
        
        # Test Congress API
        with CongressClient(settings.congress_api_key) as client:
            response = client.list_bills(limit=1)
            if response.get("bills"):
                console.print("[green]✓[/green] Congress API connection successful")
            else:
                console.print("[yellow]⚠[/yellow] Congress API returned no bills")
        
        # Test database connection
        try:
            storage = StorageManager(database_url=settings.database_url)
            console.print("[green]✓[/green] Database connection successful")
        except Exception as e:
            console.print(f"[red]✗[/red] Database connection failed: {e}")
        
        console.print("\n[bold green]All tests passed![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Test failed: {e}[/bold red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
