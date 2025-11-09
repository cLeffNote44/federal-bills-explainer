"""Database performance analysis utilities."""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class QueryStats:
    """Statistics for a database query."""
    query: str
    calls: int
    total_time: float
    mean_time: float
    max_time: float
    rows: int
    hit_percent: float  # Cache hit percentage


@dataclass
class IndexUsage:
    """Index usage statistics."""
    table_name: str
    index_name: str
    index_scans: int
    index_size: str
    table_size: str
    usage_percent: float


@dataclass
class TableStats:
    """Table statistics."""
    table_name: str
    row_count: int
    dead_rows: int
    last_vacuum: Optional[datetime]
    last_analyze: Optional[datetime]
    table_size: str
    index_size: str
    total_size: str


class DatabasePerformanceAnalyzer:
    """Analyze database performance and suggest optimizations."""
    
    def __init__(self, database_url: str):
        """Initialize analyzer with database connection."""
        self.database_url = database_url
        self.connection = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connection = psycopg2.connect(self.database_url)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.connection:
            self.connection.close()
    
    def get_slow_queries(self, min_duration_ms: float = 100, limit: int = 20) -> List[QueryStats]:
        """
        Get slow queries from pg_stat_statements.
        
        Args:
            min_duration_ms: Minimum query duration in milliseconds
            limit: Maximum number of queries to return
        """
        query = """
        SELECT 
            query,
            calls,
            total_exec_time as total_time,
            mean_exec_time as mean_time,
            max_exec_time as max_time,
            rows,
            100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
        FROM pg_stat_statements
        WHERE mean_exec_time > %s
            AND query NOT LIKE '%%pg_stat_statements%%'
            AND query NOT LIKE 'COMMIT'
            AND query NOT LIKE 'BEGIN'
        ORDER BY mean_exec_time DESC
        LIMIT %s;
        """
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (min_duration_ms, limit))
                results = cur.fetchall()
                
                return [
                    QueryStats(
                        query=row['query'][:200],  # Truncate long queries
                        calls=row['calls'],
                        total_time=row['total_time'],
                        mean_time=row['mean_time'],
                        max_time=row['max_time'],
                        rows=row['rows'],
                        hit_percent=row['hit_percent'] or 0
                    )
                    for row in results
                ]
        except psycopg2.Error as e:
            logger.warning(f"Could not get slow queries (pg_stat_statements may not be enabled): {e}")
            return []
    
    def get_missing_indexes(self) -> List[Dict[str, Any]]:
        """Identify potentially missing indexes based on query patterns."""
        query = """
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation
        FROM pg_stats
        WHERE schemaname = 'public'
            AND n_distinct > 100
            AND correlation < 0.1
            AND attname NOT IN (
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid
                WHERE a.attnum = ANY(i.indkey)
            )
        ORDER BY n_distinct DESC;
        """
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            suggestions = []
            for row in results:
                suggestions.append({
                    'table': row['tablename'],
                    'column': row['attname'],
                    'distinct_values': row['n_distinct'],
                    'correlation': row['correlation'],
                    'suggestion': f"CREATE INDEX ix_{row['tablename']}_{row['attname']} ON {row['tablename']} ({row['attname']});"
                })
            
            return suggestions
    
    def get_index_usage(self) -> List[IndexUsage]:
        """Get index usage statistics."""
        query = """
        SELECT
            t.tablename as table_name,
            indexname as index_name,
            idx_scan as index_scans,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
            pg_size_pretty(pg_relation_size(indrelid)) as table_size,
            CASE 
                WHEN idx_scan + seq_scan = 0 THEN 0
                ELSE 100.0 * idx_scan / (idx_scan + seq_scan)
            END as usage_percent
        FROM pg_stat_user_indexes
        JOIN pg_stat_user_tables t USING (schemaname, tablename)
        WHERE schemaname = 'public'
        ORDER BY usage_percent DESC;
        """
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            return [
                IndexUsage(
                    table_name=row['table_name'],
                    index_name=row['index_name'],
                    index_scans=row['index_scans'],
                    index_size=row['index_size'],
                    table_size=row['table_size'],
                    usage_percent=row['usage_percent']
                )
                for row in results
            ]
    
    def get_table_stats(self) -> List[TableStats]:
        """Get table statistics including vacuum and analyze info."""
        query = """
        SELECT
            schemaname || '.' || tablename as table_name,
            n_live_tup as row_count,
            n_dead_tup as dead_rows,
            last_vacuum,
            last_analyze,
            pg_size_pretty(pg_table_size(schemaname||'.'||tablename)) as table_size,
            pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as index_size,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            return [
                TableStats(
                    table_name=row['table_name'],
                    row_count=row['row_count'],
                    dead_rows=row['dead_rows'],
                    last_vacuum=row['last_vacuum'],
                    last_analyze=row['last_analyze'],
                    table_size=row['table_size'],
                    index_size=row['index_size'],
                    total_size=row['total_size']
                )
                for row in results
            ]
    
    def get_unused_indexes(self, min_scans: int = 50) -> List[IndexUsage]:
        """Identify unused or rarely used indexes."""
        query = """
        SELECT
            t.tablename as table_name,
            indexname as index_name,
            idx_scan as index_scans,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
            pg_size_pretty(pg_relation_size(indrelid)) as table_size,
            0 as usage_percent
        FROM pg_stat_user_indexes
        JOIN pg_stat_user_tables t USING (schemaname, tablename)
        WHERE schemaname = 'public'
            AND idx_scan < %s
            AND indexname NOT LIKE '%%_pkey'
        ORDER BY pg_relation_size(indexrelid) DESC;
        """
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (min_scans,))
            results = cur.fetchall()
            
            return [
                IndexUsage(
                    table_name=row['table_name'],
                    index_name=row['index_name'],
                    index_scans=row['index_scans'],
                    index_size=row['index_size'],
                    table_size=row['table_size'],
                    usage_percent=0
                )
                for row in results
            ]
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Run comprehensive performance analysis."""
        analysis = {
            'slow_queries': self.get_slow_queries(),
            'missing_indexes': self.get_missing_indexes(),
            'index_usage': self.get_index_usage(),
            'unused_indexes': self.get_unused_indexes(),
            'table_stats': self.get_table_stats()
        }
        
        # Add recommendations
        recommendations = []
        
        # Check for missing indexes
        if analysis['missing_indexes']:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Missing Indexes',
                'message': f"Found {len(analysis['missing_indexes'])} columns that might benefit from indexes",
                'action': 'Review suggested indexes and create those that match query patterns'
            })
        
        # Check for unused indexes
        if analysis['unused_indexes']:
            total_size = sum(
                self._parse_size(idx.index_size) 
                for idx in analysis['unused_indexes']
            )
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Unused Indexes',
                'message': f"Found {len(analysis['unused_indexes'])} unused indexes",
                'action': f'Consider dropping unused indexes to save storage'
            })
        
        # Check for tables needing vacuum
        for table in analysis['table_stats']:
            if table.dead_rows > table.row_count * 0.2:  # >20% dead rows
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Table Maintenance',
                    'message': f"Table {table.table_name} has {table.dead_rows} dead rows",
                    'action': f'Run VACUUM ANALYZE {table.table_name};'
                })
        
        # Check for slow queries
        very_slow = [q for q in analysis['slow_queries'] if q.mean_time > 1000]  # >1 second
        if very_slow:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Slow Queries',
                'message': f"Found {len(very_slow)} queries with mean time >1 second",
                'action': 'Optimize these queries or add appropriate indexes'
            })
        
        analysis['recommendations'] = recommendations
        return analysis
    
    def _parse_size(self, size_str: str) -> float:
        """Parse PostgreSQL size string to bytes."""
        if not size_str:
            return 0
        
        units = {'bytes': 1, 'kB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
        parts = size_str.split()
        if len(parts) == 2:
            value, unit = parts
            return float(value) * units.get(unit, 1)
        return 0
    
    def print_analysis(self, analysis: Optional[Dict[str, Any]] = None):
        """Print performance analysis in a formatted way."""
        if analysis is None:
            analysis = self.analyze_performance()
        
        console.print("\n[bold cyan]Database Performance Analysis[/bold cyan]\n")
        
        # Table Statistics
        if analysis['table_stats']:
            table = Table(title="Table Statistics", show_header=True)
            table.add_column("Table", style="cyan")
            table.add_column("Rows", style="green")
            table.add_column("Dead Rows", style="yellow")
            table.add_column("Table Size", style="blue")
            table.add_column("Index Size", style="blue")
            table.add_column("Total Size", style="magenta")
            
            for stat in analysis['table_stats']:
                table.add_row(
                    stat.table_name.split('.')[-1],
                    f"{stat.row_count:,}",
                    f"{stat.dead_rows:,}",
                    stat.table_size,
                    stat.index_size,
                    stat.total_size
                )
            
            console.print(table)
            console.print()
        
        # Slow Queries
        if analysis['slow_queries']:
            table = Table(title="Slow Queries (Top 5)", show_header=True)
            table.add_column("Query", style="cyan", width=50)
            table.add_column("Calls", style="green")
            table.add_column("Mean Time (ms)", style="yellow")
            table.add_column("Cache Hit %", style="blue")
            
            for query in analysis['slow_queries'][:5]:
                table.add_row(
                    query.query[:50] + "..." if len(query.query) > 50 else query.query,
                    f"{query.calls:,}",
                    f"{query.mean_time:.2f}",
                    f"{query.hit_percent:.1f}%"
                )
            
            console.print(table)
            console.print()
        
        # Missing Indexes
        if analysis['missing_indexes']:
            table = Table(title="Suggested Indexes", show_header=True)
            table.add_column("Table", style="cyan")
            table.add_column("Column", style="green")
            table.add_column("Distinct Values", style="yellow")
            
            for idx in analysis['missing_indexes'][:5]:
                table.add_row(
                    idx['table'],
                    idx['column'],
                    str(idx['distinct_values'])
                )
            
            console.print(table)
            console.print()
        
        # Recommendations
        if analysis['recommendations']:
            console.print("[bold]Recommendations:[/bold]\n")
            for rec in sorted(analysis['recommendations'], key=lambda x: x['priority']):
                color = "red" if rec['priority'] == 'HIGH' else "yellow"
                console.print(f"[{color}]● {rec['category']}:[/{color}] {rec['message']}")
                console.print(f"  Action: {rec['action']}\n")