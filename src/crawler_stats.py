"""
statistics.py
--------------
Tracks and writes statistics for the arxiv crawler project.
Statistics include:
- Number of successfully crawled papers
- Success rate
- Paper sizes before & after removing figures
- Average number of references per paper
- Reference crawl success rate
- Total runtime and average time per paper
- Memory and disk usage statistics
"""

import os
import logging
from typing import List, Tuple, Optional


class CrawlerStatistics:
    def __init__(self):
        self.total_papers = 0
        self.successful_papers = 0
        self.failed_papers = 0
        
        # List of (size_before, size_after) tuples in bytes
        self.paper_sizes: List[Tuple[int, int]] = []
        
        # List of reference counts for each paper
        self.reference_counts: List[int] = []
        
        # Track reference crawl success
        self.papers_with_references = 0
        self.papers_attempted_references = 0
        
        # Benchmark data
        self.total_runtime: float = 0.0
        self.memory_stats: Optional[dict] = None
        self.disk_stats: Optional[dict] = None
    
    def add_success(self, size_before: int, size_after: int, ref_count: int, ref_success: bool):
        """Record a successful paper crawl"""
        self.successful_papers += 1
        self.paper_sizes.append((size_before, size_after))
        self.reference_counts.append(ref_count)
        self.papers_attempted_references += 1
        if ref_success and ref_count > 0:
            self.papers_with_references += 1
    
    def add_failure(self):
        """Record a failed paper crawl"""
        self.failed_papers += 1
    
    def set_total(self, total: int):
        """Set the total number of papers to crawl"""
        self.total_papers = total
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_papers == 0:
            return 0.0
        return (self.successful_papers / self.total_papers) * 100
    
    def get_avg_size_before(self) -> float:
        """Get average paper size before cleaning (in MB)"""
        if not self.paper_sizes:
            return 0.0
        total = sum(size[0] for size in self.paper_sizes)
        return total / len(self.paper_sizes) / (1024 * 1024)  # Convert to MB
    
    def get_avg_size_after(self) -> float:
        """Get average paper size after cleaning (in MB)"""
        if not self.paper_sizes:
            return 0.0
        total = sum(size[1] for size in self.paper_sizes)
        return total / len(self.paper_sizes) / (1024 * 1024)  # Convert to MB
    
    def get_avg_references(self) -> float:
        """Get average number of references per paper"""
        if not self.reference_counts:
            return 0.0
        return sum(self.reference_counts) / len(self.reference_counts)
    
    def get_reference_success_rate(self) -> float:
        """Calculate reference crawl success rate percentage"""
        if self.papers_attempted_references == 0:
            return 0.0
        return (self.papers_with_references / self.papers_attempted_references) * 100
    
    def set_benchmark_data(self, total_runtime: float, memory_stats: dict, disk_stats: dict):
        """Set benchmark data from BenchmarkMonitor"""
        self.total_runtime = total_runtime
        self.memory_stats = memory_stats
        self.disk_stats = disk_stats
    
    def get_avg_time_per_paper(self) -> float:
        """Calculate average time per paper in seconds"""
        if self.successful_papers == 0:
            return 0.0
        return self.total_runtime / self.successful_papers
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into a readable time string"""
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.2f}m ({seconds:.2f}s)"
        else:
            hours = seconds / 3600
            minutes = (seconds % 3600) / 60
            return f"{hours:.2f}h ({minutes:.2f}m)"
    
    def write_to_file(self, filepath: str = "statistics.txt"):
        """Write all statistics to a text file in English"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("ARXIV CRAWLER STATISTICS\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Total papers attempted: {self.total_papers}\n")
            f.write(f"Successfully crawled papers: {self.successful_papers}\n")
            f.write(f"Failed papers: {self.failed_papers}\n")
            f.write(f"Success rate: {self.get_success_rate():.2f}%\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("PAPER SIZE STATISTICS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Average paper size (before removing figures): {self.get_avg_size_before():.2f} MB\n")
            f.write(f"Average paper size (after removing figures): {self.get_avg_size_after():.2f} MB\n")
            if self.get_avg_size_before() > 0:
                reduction = ((self.get_avg_size_before() - self.get_avg_size_after()) / self.get_avg_size_before()) * 100
                f.write(f"Average size reduction: {reduction:.2f}%\n")
            f.write("\n")
            
            f.write("-" * 60 + "\n")
            f.write("REFERENCE STATISTICS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Average references per paper: {self.get_avg_references():.2f}\n")
            f.write(f"Papers with references found: {self.papers_with_references}\n")
            f.write(f"Papers attempted for references: {self.papers_attempted_references}\n")
            f.write(f"Reference crawl success rate: {self.get_reference_success_rate():.2f}%\n\n")
            
            # Benchmark statistics
            if self.total_runtime > 0:
                f.write("-" * 60 + "\n")
                f.write("PERFORMANCE BENCHMARKS\n")
                f.write("-" * 60 + "\n")
                f.write(f"Total runtime: {self._format_time(self.total_runtime)}\n")
                f.write(f"Average time per paper: {self._format_time(self.get_avg_time_per_paper())}\n")
                
                if self.memory_stats:
                    f.write(f"\nMemory Usage:\n")
                    f.write(f"  Minimum: {self.memory_stats['min']:.2f} MB\n")
                    f.write(f"  Maximum: {self.memory_stats['max']:.2f} MB\n")
                    f.write(f"  Average: {self.memory_stats['avg']:.2f} MB\n")
                
                if self.disk_stats:
                    f.write(f"\nDisk Usage:\n")
                    f.write(f"  Minimum: {self.disk_stats['min']:.2f} MB\n")
                    f.write(f"  Maximum: {self.disk_stats['max']:.2f} MB\n")
                    f.write(f"  Average: {self.disk_stats['avg']:.2f} MB\n")
                
                f.write("\nNote: See benchmark_plots.png for memory and disk usage over time.\n")
                f.write("\n")
            
            f.write("=" * 60 + "\n")
        
        logging.info(f"Statistics written to {filepath}")


def get_directory_size(path: str) -> int:
    """
    Calculate total size of a directory in bytes.
    Returns 0 if directory doesn't exist.
    """
    if not os.path.exists(path):
        return 0
    
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                # Skip if it's a symbolic link
                if not os.path.islink(filepath):
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        pass  # Skip files we can't access
    except Exception as e:
        logging.warning(f"Error calculating directory size for {path}: {e}")
    
    return total_size
