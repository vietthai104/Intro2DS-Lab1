"""
benchmark.py
-------------
Benchmarking and monitoring utilities for the arxiv crawler.
Tracks:
- Total runtime
- Average time per paper
- Memory usage (min/max/avg) over time
- Disk usage (min/max/avg) over time

Logs memory and disk usage every 10 seconds to CSV for visualization.
"""

import os
import time
import csv
import threading
import psutil
import logging
from datetime import datetime
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class BenchmarkMonitor:
    """Monitor system resources during crawler execution"""
    
    def __init__(self, output_dir: str = "OUTPUT", log_interval: int = 10):
        """
        Initialize the benchmark monitor.
        
        Args:
            output_dir: Directory to monitor for disk usage
            log_interval: Interval in seconds between measurements (default: 10)
        """
        self.output_dir = output_dir
        self.log_interval = log_interval
        self.csv_file = "benchmark_data.csv"
        
        self.start_time = None
        self.end_time = None
        
        # Monitoring thread
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        # Process for memory tracking
        self.process = psutil.Process()
        
        # Data storage for statistics
        self.memory_readings = []
        self.disk_readings = []
        self.timestamps = []
    
    def start(self):
        """Start the benchmark monitoring"""
        self.start_time = time.time()
        self._stop_monitoring.clear()
        
        # Create CSV file with headers
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'elapsed_seconds', 'memory_mb', 'disk_mb'])
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logging.info(f"Benchmark monitoring started (interval: {self.log_interval}s)")
    
    def stop(self):
        """Stop the benchmark monitoring"""
        self.end_time = time.time()
        self._stop_monitoring.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        logging.info("Benchmark monitoring stopped")
    
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            mem_info = self.process.memory_info()
            return mem_info.rss / (1024 * 1024)  # Convert bytes to MB
        except Exception as e:
            logging.warning(f"Error getting memory usage: {e}")
            return 0.0
    
    def _get_disk_usage_mb(self) -> float:
        """Get current disk usage of output directory in MB"""
        try:
            if not os.path.exists(self.output_dir):
                return 0.0
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.output_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if not os.path.islink(filepath):
                        try:
                            total_size += os.path.getsize(filepath)
                        except OSError:
                            pass
            
            return total_size / (1024 * 1024)  # Convert bytes to MB
        except Exception as e:
            logging.warning(f"Error getting disk usage: {e}")
            return 0.0
    
    def _monitor_loop(self):
        """Background monitoring loop that runs every log_interval seconds"""
        if self.start_time is None:
            return
            
        while not self._stop_monitoring.is_set():
            timestamp = datetime.now()
            elapsed = time.time() - self.start_time
            memory_mb = self._get_memory_usage_mb()
            disk_mb = self._get_disk_usage_mb()
            
            # Store for statistics
            self.timestamps.append(timestamp)
            self.memory_readings.append(memory_mb)
            self.disk_readings.append(disk_mb)
            
            # Write to CSV
            try:
                with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        f"{elapsed:.2f}",
                        f"{memory_mb:.2f}",
                        f"{disk_mb:.2f}"
                    ])
            except Exception as e:
                logging.warning(f"Error writing to benchmark CSV: {e}")
            
            # Wait for next interval or until stop signal
            self._stop_monitoring.wait(self.log_interval)
    
    def get_total_runtime(self) -> float:
        """Get total runtime in seconds"""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def get_memory_stats(self) -> dict:
        """Get memory usage statistics (min/max/avg in MB)"""
        if not self.memory_readings:
            return {'min': 0.0, 'max': 0.0, 'avg': 0.0}
        
        return {
            'min': min(self.memory_readings),
            'max': max(self.memory_readings),
            'avg': sum(self.memory_readings) / len(self.memory_readings)
        }
    
    def get_disk_stats(self) -> dict:
        """Get disk usage statistics (min/max/avg in MB)"""
        if not self.disk_readings:
            return {'min': 0.0, 'max': 0.0, 'avg': 0.0}
        
        return {
            'min': min(self.disk_readings),
            'max': max(self.disk_readings),
            'avg': sum(self.disk_readings) / len(self.disk_readings)
        }
    
    def generate_visualizations(self, output_prefix: str = "benchmark"):
        """
        Generate visualization plots using pandas and matplotlib.
        Creates two plots: memory usage over time and disk usage over time.
        
        Args:
            output_prefix: Prefix for output filenames
        """
        try:
            # Read the CSV data
            df = pd.read_csv(self.csv_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Create figure with 2 subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            fig.suptitle('Crawler Benchmark - Resource Usage Over Time', fontsize=16, fontweight='bold')
            
            # Plot 1: Memory Usage
            ax1.plot(df['timestamp'], df['memory_mb'], 'b-', linewidth=2, label='Memory Usage')
            ax1.fill_between(df['timestamp'], df['memory_mb'], alpha=0.3)
            ax1.set_xlabel('Time', fontsize=12)
            ax1.set_ylabel('Memory Usage (MB)', fontsize=12)
            ax1.set_title('Memory Usage Over Time', fontsize=14)
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Format x-axis for time
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            ax1.tick_params(axis='x', rotation=45)
            
            # Add statistics annotation
            mem_stats = self.get_memory_stats()
            stats_text = f"Min: {mem_stats['min']:.1f} MB\nMax: {mem_stats['max']:.1f} MB\nAvg: {mem_stats['avg']:.1f} MB"
            ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                    fontsize=10)
            
            # Plot 2: Disk Usage
            ax2.plot(df['timestamp'], df['disk_mb'], 'g-', linewidth=2, label='Disk Usage')
            ax2.fill_between(df['timestamp'], df['disk_mb'], alpha=0.3, color='green')
            ax2.set_xlabel('Time', fontsize=12)
            ax2.set_ylabel('Disk Usage (MB)', fontsize=12)
            ax2.set_title('Disk Usage Over Time', fontsize=14)
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # Format x-axis for time
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            ax2.tick_params(axis='x', rotation=45)
            
            # Add statistics annotation
            disk_stats = self.get_disk_stats()
            stats_text = f"Min: {disk_stats['min']:.1f} MB\nMax: {disk_stats['max']:.1f} MB\nAvg: {disk_stats['avg']:.1f} MB"
            ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, 
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5),
                    fontsize=10)
            
            # Adjust layout to prevent overlap
            plt.tight_layout()
            
            # Save the figure
            output_file = f"{output_prefix}_plots.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            logging.info(f"Benchmark visualization saved to {output_file}")
            
            # Close the figure to free memory
            plt.close(fig)
            
        except Exception as e:
            logging.error(f"Error generating visualizations: {e}")


def format_time(seconds: float) -> str:
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
