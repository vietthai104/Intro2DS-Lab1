import argparse
import logging
from discovery import enumerate_ids_and_versions
from downloader import download_all_versions
from cleaner import strip_figures_and_images
from metadata import write_metadata_json
from refs import fetch_and_write_references
from utils import ensure_paper_folder, log_failed_id
from crawler_stats import CrawlerStatistics
from benchmark import BenchmarkMonitor, format_time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

def id_range(start_id: int, end_id: int, year: int = 2025, month: int = 10):
    for i in range(start_id, end_id + 1):
        yield f"{year}{month:02d}-{i:05d}"  # ví dụ 202510-00824 → 202510-05823

def run(range_from, range_to, out_root, year=2025, month=10, rate_limit=3.0):
    """
    Main crawler logic
    range_from: starting ID number (e.g., 824)
    range_to: ending ID number (e.g., 5823)
    rate_limit: wait time in seconds between requests
    """
    failed_ids_file = "failed_ids.txt"
    total = range_to - range_from + 1
    logging.info(f" Starting crawl: {total} papers from {year}{month:02d}-{range_from:05d} to {year}{month:02d}-{range_to:05d}")
    
    # Initialize statistics tracker
    stats = CrawlerStatistics()
    stats.set_total(total)
    
    # Initialize and start benchmark monitor
    monitor = BenchmarkMonitor(output_dir=out_root, log_interval=10)
    monitor.start()
    
    success_count = 0
    fail_count = 0
    
    try:
        for base_id in id_range(range_from, range_to, year, month):
            logging.info(f" Processing: {base_id}")
            try:
                paper_dir = ensure_paper_folder(out_root, base_id)  # <out_root>/yyyymm-id/
                
                # Download all versions
                versions = download_all_versions(base_id, paper_dir, rate_limit)
                if not versions:
                    logging.warning(f" No versions found for {base_id}")
                    log_failed_id(failed_ids_file, base_id, "No versions found")
                    stats.add_failure()
                    fail_count += 1
                    continue
                
                # Clean up figures and images (get size before and after)
                size_before, size_after = strip_figures_and_images(paper_dir)
                
                # Write metadata
                write_metadata_json(base_id, paper_dir, versions)
                
                # Fetch references (get count and success status)
                ref_count, ref_success = fetch_and_write_references(base_id, paper_dir, rate_limit=rate_limit)
                
                # Record success with statistics
                stats.add_success(size_before, size_after, ref_count, ref_success)
                
                success_count += 1
                logging.info(f"Successfully processed {base_id} ({success_count}/{total})")
                
            except Exception as e:
                logging.error(f" Failed to process {base_id}: {e}")
                log_failed_id(failed_ids_file, base_id, str(e))
                stats.add_failure()
                fail_count += 1
    
    finally:
        # Stop benchmark monitoring
        monitor.stop()
        
        # Get benchmark statistics
        total_runtime = monitor.get_total_runtime()
        memory_stats = monitor.get_memory_stats()
        disk_stats = monitor.get_disk_stats()
        
        # Set benchmark data in statistics
        stats.set_benchmark_data(total_runtime, memory_stats, disk_stats)
        
        logging.info(f"Completed! Success: {success_count}, Failed: {fail_count}")
        logging.info(f"Total runtime: {format_time(total_runtime)}")
        
        # Generate visualizations
        logging.info("Generating benchmark visualizations...")
        monitor.generate_visualizations()
        
        # Write statistics to file
        stats.write_to_file("statistics.txt")
        logging.info("Statistics saved to statistics.txt")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", type=int, required=True, help="Starting ID number (e.g., 824)")
    ap.add_argument("--to",   dest="end",   type=int, required=True, help="Ending ID number (e.g., 5823)")
    ap.add_argument("--out",  dest="out",   default="OUTPUT", help="Output directory")
    ap.add_argument("--wait", dest="wait",  type=float, default=3.0, help="Wait time in seconds between requests")
    args = ap.parse_args()
    run(args.start, args.end, args.out, year=2025, month=10, 
        rate_limit=args.wait)
