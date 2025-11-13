import json, arxiv
from datetime import datetime
import os
import logging

def _to_iso(dt):
    """Convert datetime to ISO date string"""
    if isinstance(dt, datetime): 
        return dt.date().isoformat()
    return str(dt) if dt else None

def _convert_id_format(base_id: str):
    """
    Convert from format '202510-00824' to '2510.00824' for arXiv API
    """
    parts = base_id.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid base_id format: {base_id}")
    
    yyyymm = parts[0]
    nnnnn = parts[1]
    
    year = yyyymm[:4]
    month = yyyymm[4:6]
    
    yy = year[2:]
    return f"{yy}{month}.{nnnnn}"

def write_metadata_json(base_id: str, paper_dir: str, versions: list):
    """
    Write metadata.json for a paper
    base_id: format '202510-00824'
    versions: list like ['202510-00824v1', '202510-00824v2']
    """
    try:
        # Use client with no retries - we'll handle errors gracefully
        client = arxiv.Client(
            page_size=1,
            delay_seconds=3.0,
            num_retries=0  # Disable retries for faster failure
        )
        
        # Get metadata from the latest version
        if versions:
            # Extract version number from last version (e.g., '202510-00824v2' -> 'v2')
            last_ver = versions[-1]
            ver_num = last_ver.split('v')[-1]
            api_id = _convert_id_format(base_id) + f"v{ver_num}"
        else:
            api_id = _convert_id_format(base_id)
        
        logging.info(f"  Fetching metadata for {api_id}")
        search = arxiv.Search(id_list=[api_id])
        paper = next(client.results(search))
        
        data = {
            "title": paper.title,
            "authors": [a.name for a in paper.authors],
            "submission_date": _to_iso(paper.published),
            "revised_dates": [_to_iso(paper.updated)] if paper.updated and paper.updated != paper.published else [],
            "venue": paper.journal_ref or "arXiv preprint",
            "versions": versions
        }
        
        with open(os.path.join(paper_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"  Saved metadata.json")
        
    except Exception as e:
        logging.error(f"  Error writing metadata for {base_id}: {e}")
        # Write minimal metadata
        data = {
            "title": "Unknown",
            "authors": [],
            "submission_date": None,
            "revised_dates": [],
            "venue": "arXiv preprint",
            "versions": versions
        }
        with open(os.path.join(paper_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
