#!/usr/bin/env python3
"""
Parallel Processor for Torob Scraper.
Handles concurrent processing of multiple parts for improved performance.
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from core.config_manager import get_config


class ParallelProcessor:
    """Handles parallel processing of multiple parts."""
    
    def __init__(self):
        """Initialize the parallel processor."""
        self.config = get_config()
        self.performance_config = self.config.get('performance', {})
        self.parallel_config = self.performance_config.get('parallel', {})
        
        # Parallel processing settings
        self.enabled = self.parallel_config.get('enabled', True)
        self.max_workers = self.parallel_config.get('max_workers', 3)
        self.batch_size = self.parallel_config.get('batch_size', 5)
        
        # Progress tracking
        self.progress_config = self.performance_config.get('progress', {})
        self.show_progress = self.progress_config.get('enabled', True)
        self.update_interval = self.progress_config.get('update_interval', 1)
        self.show_eta = self.progress_config.get('show_eta', True)
        
        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Thread lock for stats updates
        self._lock = threading.Lock()
    
    def _update_stats(self, completed: int = 0, failed: int = 0) -> None:
        """Update statistics in a thread-safe manner."""
        with self._lock:
            self.stats['completed_tasks'] += completed
            self.stats['failed_tasks'] += failed
    
    def _calculate_eta(self) -> Optional[float]:
        """Calculate estimated time remaining."""
        if not self.stats['start_time'] or self.stats['completed_tasks'] == 0:
            return None
        
        elapsed = time.time() - self.stats['start_time']
        rate = self.stats['completed_tasks'] / elapsed
        remaining = self.stats['total_tasks'] - self.stats['completed_tasks']
        
        return remaining / rate if rate > 0 else None
    
    def _format_time(self, seconds: float) -> str:
        """Format time in a human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    def _print_progress(self) -> None:
        """Print progress information."""
        if not self.show_progress:
            return
        
        completed = self.stats['completed_tasks']
        total = self.stats['total_tasks']
        failed = self.stats['failed_tasks']
        
        if total == 0:
            return
        
        percentage = (completed / total) * 100
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        
        # Calculate ETA
        eta_str = ""
        if self.show_eta and completed > 0:
            eta = self._calculate_eta()
            if eta:
                eta_str = f" | ETA: {self._format_time(eta)}"
        
        print(f"\r🔄 Progress: {completed}/{total} ({percentage:.1f}%) | "
              f"Failed: {failed} | Elapsed: {self._format_time(elapsed)}{eta_str}", 
              end="", flush=True)
    
    async def process_parts_parallel(self, 
                                   parts_data: List[Dict[str, Any]], 
                                   process_func: Callable[[Dict[str, Any]], Any]) -> List[Any]:
        """
        Process multiple parts in parallel.
        
        Args:
            parts_data: List of part data dictionaries
            process_func: Function to process each part
            
        Returns:
            List of results from processing each part
        """
        if not self.enabled or len(parts_data) <= 1:
            # Process sequentially if parallel processing is disabled or only one part
            results = []
            for part_data in parts_data:
                result = await process_func(part_data)
                results.append(result)
            return results
        
        # Initialize statistics
        self.stats = {
            'total_tasks': len(parts_data),
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': time.time(),
            'end_time': None
        }
        
        print(f"🚀 Starting parallel processing of {len(parts_data)} parts")
        print(f"   Workers: {self.max_workers}, Batch size: {self.batch_size}")
        
        # Process in batches
        all_results = []
        for i in range(0, len(parts_data), self.batch_size):
            batch = parts_data[i:i + self.batch_size]
            batch_results = await self._process_batch(batch, process_func)
            all_results.extend(batch_results)
        
        # Final statistics
        self.stats['end_time'] = time.time()
        total_time = self.stats['end_time'] - self.stats['start_time']
        
        print(f"\n✅ Parallel processing completed!")
        print(f"   Total time: {self._format_time(total_time)}")
        print(f"   Completed: {self.stats['completed_tasks']}/{self.stats['total_tasks']}")
        print(f"   Failed: {self.stats['failed_tasks']}")
        
        if self.stats['completed_tasks'] > 0:
            avg_time = total_time / self.stats['completed_tasks']
            print(f"   Average time per part: {self._format_time(avg_time)}")
        
        return all_results
    
    async def _process_batch(self, 
                           batch: List[Dict[str, Any]], 
                           process_func: Callable[[Dict[str, Any]], Any]) -> List[Any]:
        """
        Process a batch of parts concurrently.
        
        Args:
            batch: List of part data dictionaries
            process_func: Function to process each part
            
        Returns:
            List of results from processing the batch
        """
        # Create tasks for the batch
        tasks = []
        for part_data in batch:
            task = asyncio.create_task(self._process_single_part(part_data, process_func))
            tasks.append(task)
        
        # Wait for all tasks in the batch to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and update statistics
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"\n❌ Error processing part {i+1}: {result}")
                self._update_stats(failed=1)
                processed_results.append(None)
            else:
                self._update_stats(completed=1)
                processed_results.append(result)
        
        return processed_results
    
    async def _process_single_part(self, 
                                 part_data: Dict[str, Any], 
                                 process_func: Callable[[Dict[str, Any]], Any]) -> Any:
        """
        Process a single part with error handling.
        
        Args:
            part_data: Part data dictionary
            process_func: Function to process the part
            
        Returns:
            Result from processing the part
        """
        try:
            return await process_func(part_data)
        except Exception as e:
            print(f"\n❌ Error processing part {part_data.get('part_name', 'Unknown')}: {e}")
            raise e
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            stats['total_time'] = stats['end_time'] - stats['start_time']
        elif stats['start_time']:
            stats['total_time'] = time.time() - stats['start_time']
        else:
            stats['total_time'] = 0
        
        if stats['completed_tasks'] > 0 and stats['total_time'] > 0:
            stats['avg_time_per_task'] = stats['total_time'] / stats['completed_tasks']
        else:
            stats['avg_time_per_task'] = 0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': None,
            'end_time': None
        }


# Global parallel processor instance
parallel_processor = ParallelProcessor()

def get_parallel_processor() -> ParallelProcessor:
    """Get the global parallel processor instance."""
    return parallel_processor
