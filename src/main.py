import argparse
from discovery import enumerate_ids_and_versions
from downloader import download_all_versions
from cleaner import strip_figures_and_images
from metadata import write_metadata_json, write_bibtex
from refs import fetch_and_write_references
from utils import ensure_paper_folder


def id_range(start_id: int, end_id: int, year: int = 2025, month: int = 10):
    for i in range(start_id, end_id + 1):
        yield f"{year}{month:02d}-{i:05d}"  # ví dụ 202510-00824 → 202510-05823

def run(range_from, range_to, out_root, rate_limit=1.0, workers=2):
    for base_id in id_range(824, 5823, 2025, 10):
        paper_dir = ensure_paper_folder(out_root, base_id)  # <out_root>/yyyymm-id/
        versions = download_all_versions(base_id, paper_dir, rate_limit, workers)
        for ver in versions:
            strip_figures_and_images(paper_dir)  # áp dụng trên toàn bộ tex/
        write_metadata_json(base_id, paper_dir, versions)
        write_bibtex(base_id, paper_dir)
        fetch_and_write_references(base_id, paper_dir, rate_limit=1.0)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", required=True, help="e.g., 2310.10000")
    ap.add_argument("--to",   dest="end",   required=True, help="e.g., 2310.10100")
    ap.add_argument("--out",  dest="out",   default="OUTPUT")
    ap.add_argument("--rps",  dest="rps",   type=float, default=1.0, help="requests per second (API)")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    run(args.start, args.end, args.out, rate_limit=args.rps, workers=args.workers)
