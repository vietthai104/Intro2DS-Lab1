import arxiv, time, os
import logging
import requests
from urllib.parse import urlparse

def _safe_download(paper, dirpath, filename, rate_limit):
    """Download source file with rate limiting"""
    os.makedirs(dirpath, exist_ok=True)
    
    # Try using the arxiv library's download method first
    try:
        paper.download_source(dirpath=dirpath, filename=filename)
        # Add extra delay to respect arXiv rate limits
        delay = max(3.0, 1.0/max(rate_limit, 0.1))
        time.sleep(delay)
        return True
    except (AttributeError, TypeError) as e:
        # The arxiv library's method failed - try manual download
        logging.debug(f"  arxiv library download failed: {e}, trying manual download")
        
        # Construct the source URL manually
        # arXiv source format: https://arxiv.org/e-print/YYMM.NNNNN
        try:
            # Get the paper ID from the entry_id
            paper_id = paper.entry_id.split('/abs/')[-1]  # e.g., "2510.01000v1"
            base_id = paper_id.split('v')[0]  # Remove version: "2510.01000"
            
            source_url = f"https://arxiv.org/e-print/{base_id}"
            logging.debug(f"  Attempting manual download from: {source_url}")
            
            response = requests.get(source_url, timeout=30)
            if response.status_code == 200:
                filepath = os.path.join(dirpath, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                time.sleep(1.0/max(rate_limit, 0.1))
                return True
            else:
                logging.warning(f"  Source not available (HTTP {response.status_code})")
                return False
        except Exception as manual_error:
            logging.error(f"  Manual download also failed: {manual_error}")
            return False
    except Exception as e:
        logging.error(f"  Download failed: {e}")
        return False

def _convert_id_format(base_id: str):
    """
    Convert from format '202510-00824' to '2025.10.00824' for arXiv API
    """
    # base_id format: yyyymm-nnnnn (e.g., "202510-00824")
    parts = base_id.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid base_id format: {base_id}")
    
    yyyymm = parts[0]
    nnnnn = parts[1]
    
    # Extract year and month
    year = yyyymm[:4]
    month = yyyymm[4:6]
    
    # Return arXiv API format: YYMM.NNNNN
    yy = year[2:]  # Get last 2 digits of year
    return f"{yy}{month}.{nnnnn}"

def download_all_versions(base_id:str, paper_dir:str, rate_limit:float):
    """
    Download all versions of a paper directly without searching.
    base_id: format '202510-00824'
    Returns: list of version strings like ['202510-00824v1', '202510-00824v2']
    """
    versions = []
    
    # Convert to arXiv API format
    api_id = _convert_id_format(base_id)
    logging.info(f"  Downloading versions for {base_id} (API ID: {api_id})")
    
    tex_dir = os.path.join(paper_dir, "tex")
    os.makedirs(tex_dir, exist_ok=True)
    
    for v in range(1, 11):  # Try up to 10 versions
        vid_api = f"{api_id}v{v}"  # API format: 2510.00824v1
        vid_save = f"{base_id}v{v}"  # Save format: 202510-00824v1
        
        # Construct direct download URL
        source_url = f"https://arxiv.org/e-print/{vid_api}"
        filename = f"{vid_save}.tar.gz"
        filepath = os.path.join(tex_dir, filename)
        
        # Manual retry with exponential backoff
        max_retries = 3
        retry_delay = 5.0
        
        for attempt in range(max_retries):
            try:
                logging.debug(f"  Downloading from: {source_url}")
                response = requests.get(source_url, timeout=30)
                
                if response.status_code == 200:
                    # Successful download
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    versions.append(vid_save)
                    logging.info(f" Downloaded {vid_save}")
                    time.sleep(max(3.0, rate_limit))
                    break  # Success - move to next version
                    
                elif response.status_code == 404:
                    # Version doesn't exist
                    if v == 1:
                        logging.warning(f"  No versions found for {base_id}")
                    else:
                        logging.debug(f"  No more versions after v{v-1}")
                    return versions
                    
                elif response.status_code == 429:
                    # Rate limited
                    if attempt < max_retries - 1:
                        backoff = retry_delay * (2 ** attempt)  # Exponential backoff: 5s, 10s, 20s
                        logging.warning(f"  Rate limited on {vid_api} (attempt {attempt + 1}/{max_retries}). Backing off for {backoff:.1f}s...")
                        time.sleep(backoff)
                    else:
                        logging.error(f"  Failed after {max_retries} attempts due to rate limiting: {vid_api}")
                        return versions
                        
                else:
                    # Other HTTP error
                    logging.warning(f"  HTTP {response.status_code} for {vid_api}")
                    if v == 1:
                        logging.warning(f"  No versions found for {base_id}")
                    return versions
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    logging.warning(f"  Timeout on {vid_api} (attempt {attempt + 1}/{max_retries}). Retrying...")
                    time.sleep(retry_delay)
                else:
                    logging.error(f"  Timeout after {max_retries} attempts: {vid_api}")
                    return versions
                    
            except Exception as e:
                logging.error(f"  Error downloading {vid_api}: {e}")
                if v == 1:
                    return versions
                else:
                    return versions
    
    # Add delay between papers to avoid hitting rate limits
    time.sleep(max(3.0, rate_limit))
    return versions
