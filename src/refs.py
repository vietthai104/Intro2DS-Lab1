import requests, time, os, json
import logging
from collections import deque

API_KEY="fABIqrnFje8MkJv1UAQPo2I2XNDxTdozrSYa2yXj"

# Track Semantic Scholar API calls for rate limiting
# Limit: 1 req/sec
_api_call_times = deque(maxlen=1)

def _wait_for_rate_limit():
    """
    Enforce Semantic Scholar API rate limits:
    - 1 request per second
    """
    current_time = time.time()
    
    # Check 1 request per second limit
    if _api_call_times:
        time_since_last = current_time - _api_call_times[-1]
        if time_since_last < 1.0:
            sleep_time = 1.0 - time_since_last
            time.sleep(sleep_time)
            current_time = time.time()
    
    # Record this call
    _api_call_times.append(current_time)

def _convert_id_format(base_id: str):
    """
    Convert from format '202510-00824' to '2510.00824' for Semantic Scholar API
    """
    parts = base_id.split("-")
    if len(parts) != 2:
        return base_id  # Return as-is if format is unexpected
    
    yyyymm = parts[0]
    nnnnn = parts[1]
    
    # Extract year and month
    year = yyyymm[:4]
    month = yyyymm[4:6]
    
    # Return format: YYMM.NNNNN (e.g., 2510.00824)
    yy = year[2:]
    return f"{yy}{month}.{nnnnn}"

def _parse_arxiv_id(arxiv_id: str):
    """
    Parse arXiv ID from Semantic Scholar format (e.g., '2510.00824') to our format '202510-00824'
    """
    try:
        # Handle format YYMM.NNNNN or YYYYMM.NNNNN
        if '.' not in arxiv_id:
            return None
        
        parts = arxiv_id.split('.')
        yymm = parts[0]
        nnnnn = parts[1].split('v')[0]  # Remove version if present
        
        # Convert YYMM to YYYYMM
        if len(yymm) == 4:  # YYMM format
            yy = yymm[:2]
            mm = yymm[2:]
            # Assume 20xx for now (2000-2099)
            yyyy = "20" + yy
        elif len(yymm) == 6:  # YYYYMM format
            yyyy = yymm[:4]
            mm = yymm[4:]
        else:
            return None
        
        return f"{yyyy}{mm}-{nnnnn}"
    except Exception as e:
        logging.warning(f"  Failed to parse arXiv ID '{arxiv_id}': {e}")
        return None

def fetch_and_write_references(base_id: str, paper_dir: str, rate_limit=1.0):
    """
    Fetch references from Semantic Scholar API and save to references.json
    base_id: format '202510-00824'
    
    Returns:
        tuple: (reference_count, success) where success is True if API call succeeded
    """
    # Convert to API format (2510.00824)
    api_id = _convert_id_format(base_id)
    
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{api_id}"
    params = {"fields": "references,references.externalIds,references.title,references.authors,references.year"}
    headers = {"x-api-key": API_KEY}
    
    refs = {}
    api_success = False
    
    try:
        logging.info(f"  Fetching references from Semantic Scholar for {base_id}")
        
        # Wait for rate limit before making the call
        _wait_for_rate_limit()
        
        r = requests.get(url, params=params, headers=headers, timeout=30)
        
        # Handle 429 with retries
        retry_count = 0
        max_retries = 10  # High number for continuous retry
        while r.status_code == 429 and retry_count < max_retries:
            retry_count += 1
            wait_time = 5
            logging.warning(f"  Rate limit hit (429), retry {retry_count}, waiting {wait_time}s...")
            time.sleep(wait_time)
            _wait_for_rate_limit()
            r = requests.get(url, params=params, headers=headers, timeout=30)
        
        if r.ok:
            api_success = True
            data = r.json()
            ref_list = data.get("references") or []
            logging.info(f"  Found {len(ref_list)} references")
            
            for ref in ref_list:
                ext = (ref.get("externalIds") or {})
                arx = ext.get("ArXiv")
                
                if arx:
                    # Parse arXiv ID
                    parsed_id = _parse_arxiv_id(arx)
                    if parsed_id:
                        authors = [a.get("name") for a in (ref.get("authors") or []) if a.get("name")]
                        refs[parsed_id] = {
                            "title": ref.get("title"),
                            "authors": authors,
                            "submission_date": None,   # Semantic Scholar doesn't provide this
                            "revised_dates": []
                        }
        else:
            logging.warning(f"  Semantic Scholar API returned status {r.status_code} for {base_id}")
            
    except requests.exceptions.Timeout:
        logging.error(f"  Timeout fetching references for {base_id}")
    except Exception as e:
        logging.error(f"  Error fetching references for {base_id}: {e}")
    
    # Write references.json
    with open(os.path.join(paper_dir, "references.json"), "w", encoding="utf-8") as f:
        json.dump(refs, f, ensure_ascii=False, indent=2)
    
    logging.info(f"  Saved {len(refs)} references to references.json")
    
    return (len(refs), api_success)
