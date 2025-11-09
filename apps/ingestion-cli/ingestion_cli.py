#!/usr/bin/env python3
import typer
from rich.console import Console
from rich.table import Table
from fbx_core.db.session import SessionLocal
from fbx_core.providers.congress_gov import CongressGovProvider
from fbx_core.services.ingestion import IngestionService

app = typer.Typer()
console = Console()

@app.command()
def run():
    """Run the ingestion pipeline."""
    console.print("[bold blue]Starting ingestion pipeline...[/bold blue]")
    
    with SessionLocal() as session:
        provider = CongressGovProvider()
        service = IngestionService(provider, session)
        
        try:
            count = service.run()
            console.print(f"[bold green]✅ Successfully ingested {count} bills[/bold green]")
        except Exception as e:
            console.print(f"[bold red]❌ Ingestion failed: {e}[/bold red]")
            raise typer.Exit(code=1)

@app.command()
def test_fixtures():
    """Test ingestion with fixture data only."""
    console.print("[yellow]Testing with fixture data (DRY_RUN=true)...[/yellow]")
    
    with SessionLocal() as session:
        provider = CongressGovProvider(fixtures_dir="fixtures")
        service = IngestionService(provider, session)
        
        # Force dry-run mode and disable heavy features
        service.settings.dry_run = True
        service.settings.explanations_enabled = False
        service.settings.embeddings_enabled = False
        
        try:
            count = service.run()
            console.print(f"[green]✅ Test completed: processed {count} fixture bills[/green]")
        except Exception as e:
            console.print(f"[red]❌ Test failed: {e}[/red]")
            raise typer.Exit(code=1)

@app.command()
def status():
    """Show ingestion status and bill counts."""
    from sqlalchemy import select, func
    from fbx_core.models.tables import Bill, IngestionState
    
    with SessionLocal() as session:
        bill_count = session.scalar(select(func.count()).select_from(Bill))
        state = session.get(IngestionState, 1)
        
        table = Table(title="Ingestion Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Bills", str(bill_count or 0))
        table.add_row("Last Run", str(state.last_run_at) if state else "Never")
        
        console.print(table)

if __name__ == "__main__":
    app()
