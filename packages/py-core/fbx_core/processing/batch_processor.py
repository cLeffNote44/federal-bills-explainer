"""Batch processing with parallelization for efficient bill processing."""

import asyncio
import concurrent.futures
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
import logging
from threading import Lock
import time
from queue import Queue, Empty
import multiprocessing as mp

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    batch_size: int = 10
    max_workers: int = 4
    use_multiprocessing: bool = False
    timeout_per_item: float = 30.0
    retry_failed: bool = True
    progress_bar: bool = True


@dataclass 
class BatchResult:
    """Result of batch processing."""
    total: int
    successful: int
    failed: int
    skipped: int
    duration: float
    errors: List[Dict[str, Any]]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total == 0:
            return 0.0
        return (self.successful / self.total) * 100


class BatchProcessor:
    """Process items in batches with parallelization."""
    
    def __init__(self, config: Optional[BatchConfig] = None):
        """Initialize batch processor."""
        self.config = config or BatchConfig()
        self.stats_lock = Lock()
        self.stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
    
    def process_batch(
        self,
        items: List[Any],
        process_func: Callable[[Any], Any],
        description: str = "Processing"
    ) -> BatchResult:
        """
        Process items in batches with parallelization.
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            description: Description for progress bar
            
        Returns:
            BatchResult with processing statistics
        """
        start_time = time.time()
        self.reset_stats()
        
        if not items:
            return BatchResult(0, 0, 0, 0, 0.0, [])
        
        # Split into batches
        batches = self._create_batches(items)
        total_items = len(items)
        
        if self.config.progress_bar:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"[cyan]{description}",
                    total=total_items
                )
                
                # Process batches
                for batch in batches:
                    self._process_batch_parallel(batch, process_func)
                    progress.update(task, advance=len(batch))
        else:
            # Process without progress bar
            for batch in batches:
                self._process_batch_parallel(batch, process_func)
        
        duration = time.time() - start_time
        
        return BatchResult(
            total=total_items,
            successful=self.stats['successful'],
            failed=self.stats['failed'],
            skipped=self.stats['skipped'],
            duration=duration,
            errors=self.stats['errors']
        )
    
    async def process_batch_async(
        self,
        items: List[Any],
        process_func: Callable[[Any], asyncio.Future],
        description: str = "Processing"
    ) -> BatchResult:
        """
        Process items asynchronously in batches.
        
        Args:
            items: List of items to process
            process_func: Async function to process each item
            description: Description for progress bar
            
        Returns:
            BatchResult with processing statistics
        """
        start_time = time.time()
        self.reset_stats()
        
        if not items:
            return BatchResult(0, 0, 0, 0, 0.0, [])
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.max_workers)
        
        async def process_with_semaphore(item):
            async with semaphore:
                return await self._process_item_async(item, process_func)
        
        # Process all items concurrently with limit
        tasks = [process_with_semaphore(item) for item in items]
        
        if self.config.progress_bar:
            # Show progress
            completed = 0
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"[cyan]{description}",
                    total=len(items)
                )
                
                # Process tasks as they complete
                for coro in asyncio.as_completed(tasks):
                    await coro
                    completed += 1
                    progress.update(task, completed=completed)
        else:
            # Process without progress
            await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        return BatchResult(
            total=len(items),
            successful=self.stats['successful'],
            failed=self.stats['failed'],
            skipped=self.stats['skipped'],
            duration=duration,
            errors=self.stats['errors']
        )
    
    def _create_batches(self, items: List[Any]) -> List[List[Any]]:
        """Split items into batches."""
        batch_size = self.config.batch_size
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    def _process_batch_parallel(self, batch: List[Any], process_func: Callable):
        """Process a batch in parallel."""
        if self.config.use_multiprocessing:
            # Use process pool
            with mp.Pool(processes=self.config.max_workers) as pool:
                results = pool.map(process_func, batch)
                self._update_stats_from_results(results, batch)
        else:
            # Use thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = {
                    executor.submit(self._process_item_safe, item, process_func): item
                    for item in batch
                }
                
                for future in concurrent.futures.as_completed(futures):
                    item = futures[future]
                    try:
                        result = future.result(timeout=self.config.timeout_per_item)
                        self._update_stats(result, item)
                    except Exception as e:
                        self._record_error(item, e)
    
    def _process_item_safe(self, item: Any, process_func: Callable) -> Dict[str, Any]:
        """Safely process an item with error handling."""
        try:
            result = process_func(item)
            return {'success': True, 'result': result}
        except Exception as e:
            logger.error(f"Error processing item: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _process_item_async(self, item: Any, process_func: Callable) -> Dict[str, Any]:
        """Process item asynchronously."""
        try:
            result = await process_func(item)
            with self.stats_lock:
                self.stats['successful'] += 1
                self.stats['processed'] += 1
            return {'success': True, 'result': result}
        except asyncio.TimeoutError:
            self._record_error(item, "Timeout")
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            self._record_error(item, e)
            return {'success': False, 'error': str(e)}
    
    def _update_stats(self, result: Dict[str, Any], item: Any):
        """Update statistics based on result."""
        with self.stats_lock:
            self.stats['processed'] += 1
            
            if result.get('success'):
                self.stats['successful'] += 1
            else:
                self.stats['failed'] += 1
                if result.get('error'):
                    self.stats['errors'].append({
                        'item': str(item)[:100],
                        'error': result['error']
                    })
    
    def _update_stats_from_results(self, results: List[Any], batch: List[Any]):
        """Update stats from processing results."""
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self._record_error(batch[i], result)
            else:
                with self.stats_lock:
                    self.stats['successful'] += 1
                    self.stats['processed'] += 1
    
    def _record_error(self, item: Any, error: Any):
        """Record processing error."""
        with self.stats_lock:
            self.stats['failed'] += 1
            self.stats['processed'] += 1
            self.stats['errors'].append({
                'item': str(item)[:100],
                'error': str(error)
            })
        
        logger.error(f"Failed to process item: {error}")
    
    def reset_stats(self):
        """Reset processing statistics."""
        with self.stats_lock:
            self.stats = {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'errors': []
            }


class QueueBatchProcessor:
    """Queue-based batch processor for continuous processing."""
    
    def __init__(self, config: Optional[BatchConfig] = None):
        """Initialize queue processor."""
        self.config = config or BatchConfig()
        self.queue = Queue()
        self.workers = []
        self.running = False
        self.stats = BatchProcessor(config).stats
    
    def start_workers(self, process_func: Callable):
        """Start worker threads."""
        self.running = True
        
        for i in range(self.config.max_workers):
            worker = threading.Thread(
                target=self._worker,
                args=(process_func,),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {self.config.max_workers} workers")
    
    def _worker(self, process_func: Callable):
        """Worker thread to process queue items."""
        while self.running:
            try:
                item = self.queue.get(timeout=1)
                
                if item is None:  # Poison pill
                    break
                
                try:
                    process_func(item)
                    with self.stats_lock:
                        self.stats['successful'] += 1
                except Exception as e:
                    logger.error(f"Worker error: {e}")
                    with self.stats_lock:
                        self.stats['failed'] += 1
                finally:
                    self.queue.task_done()
                    
            except Empty:
                continue
    
    def add_items(self, items: List[Any]):
        """Add items to processing queue."""
        for item in items:
            self.queue.put(item)
    
    def stop_workers(self):
        """Stop all workers."""
        self.running = False
        
        # Send poison pills
        for _ in self.workers:
            self.queue.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers.clear()
        logger.info("All workers stopped")
    
    def wait_completion(self):
        """Wait for all queued items to be processed."""
        self.queue.join()


def create_optimized_processor(
    num_items: int,
    cpu_bound: bool = False
) -> BatchProcessor:
    """
    Create an optimized batch processor based on workload.
    
    Args:
        num_items: Number of items to process
        cpu_bound: Whether the work is CPU-bound
        
    Returns:
        Configured BatchProcessor
    """
    # Determine optimal configuration
    cpu_count = mp.cpu_count()
    
    if cpu_bound:
        # CPU-bound: use multiprocessing
        config = BatchConfig(
            batch_size=max(10, num_items // (cpu_count * 4)),
            max_workers=cpu_count,
            use_multiprocessing=True
        )
    else:
        # I/O-bound: use threading
        config = BatchConfig(
            batch_size=min(50, max(10, num_items // 10)),
            max_workers=min(cpu_count * 2, 8),
            use_multiprocessing=False
        )
    
    return BatchProcessor(config)