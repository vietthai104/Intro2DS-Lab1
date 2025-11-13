# ArXiv Data Crawler

A Python-based data crawler for downloading and processing arXiv papers. This project downloads LaTeX source files, metadata, BibTeX citations, and references for papers in a specified ID range.

## Project Overview

This crawler is designed to:
- Download all versions of arXiv papers in a specified range
- Extract LaTeX source files and remove images to reduce storage
- Collect paper metadata (title, authors, dates, venue)
- Generate BibTeX citations
- Fetch references from Semantic Scholar API

**Target Range:** Papers from `2025.10.00824` to `2025.10.05823` (5000 papers)

## How to Run

python src/main.py --from 824 --to 1323 --year 2025 --month 10 --out 20120187 --wait 3.0


### Command-Line Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--from` | int | Yes | - | Starting ID number (e.g., 824) |
| `--to` | int |  Yes | - | Ending ID number (e.g., 5823) |
| `--out` | str | No | OUTPUT | Output directory path |
| `--wait` | float | No | 3.0 | Wait time in seconds between requests |

## File Structure & Functionality

### Core Files

#### `src/main.py`
**Purpose:** Main entry point and orchestration

**What it does:**
- Parses command-line arguments
- Orchestrates the entire crawling pipeline
- Loops through each paper ID in the specified range
- Calls other modules in sequence: download → clean → metadata → references
- Handles errors and logs failed IDs to `failed_ids.txt`
- Reports progress and statistics

**Key functions:**
- `id_range(start_id, end_id, year, month)` - Generates paper IDs in format `yyyymm-nnnnn`
- `run(...)` - Main pipeline execution

---

#### `src/downloader.py`
**Purpose:** Download LaTeX source files from arXiv

**What it does:**
- Converts internal ID format (`202510-00824`) to arXiv API format (`2510.00824`)
- Attempts to download all versions of each paper (v1, v2, v3, ...)
- Saves `.tar.gz` source archives to the `tex/` directory
- Implements rate limiting to respect arXiv API limits

**Key functions:**
- `_convert_id_format(base_id)` - Converts ID formats
- `download_all_versions(base_id, paper_dir, rate_limit)` - Downloads all versions
- `_safe_download(paper, dirpath, filename, rate_limit)` - Downloads with rate limiting

**API Used:** `arxiv` Python library

---

#### `src/cleaner.py`
**Purpose:** Clean LaTeX source files to reduce storage

**What it does:**
- Extracts all `.tar.gz` archives in the `tex/` directory
- Removes image files (`.png`, `.jpg`, `.pdf`, `.eps`, `.svg`, `.tif`, `.bmp`, etc.)
- Strips figure environments (`\begin{figure}...\end{figure}`) from `.tex` files
- Removes `\includegraphics` commands from `.tex` files
- Handles both compressed and uncompressed tar files

**Key functions:**
- `strip_figures_and_images(paper_dir)` - Main cleaning function
- `_extract_all_tars(tex_dir)` - Extracts tar archives
- `_remove_images(tex_dir)` - Deletes image files
- `_strip_tex(tex_dir)` - Removes figure commands from LaTeX

---

#### `src/metadata.py`
**Purpose:** Extract and save paper metadata

**What it does:**
- Fetches paper metadata from arXiv API (title, authors, dates, venue)
- Saves metadata to `metadata.json` with proper formatting
- Generates BibTeX citation in `references.bib` with actual paper information
- Handles multiple versions and revision dates

**Key functions:**
- `write_metadata_json(base_id, paper_dir, versions)` - Creates metadata.json
- `write_bibtex(base_id, paper_dir)` - Creates references.bib
- `_convert_id_format(base_id)` - Converts ID for API calls
- `_to_iso(dt)` - Converts datetime to ISO format

**Output files:**
- `metadata.json` - Complete paper metadata
---

#### `src/refs.py`
**Purpose:** Fetch paper references from Semantic Scholar

**What it does:**
- Queries Semantic Scholar API for paper references
- Filters references to include only arXiv papers
- Converts arXiv IDs from API format back to internal format
- Saves references to `references.json`
- Handles API errors and timeouts gracefully

**Key functions:**
- `fetch_and_write_references(base_id, paper_dir, rate_limit)` - Main reference fetching
- `_convert_id_format(base_id)` - Converts to API format
- `_parse_arxiv_id(arxiv_id)` - Parses arXiv IDs from responses

**API Used:** Semantic Scholar Graph API

**Output file:**
- `references.json` - Dictionary of referenced papers with metadata

---

#### `src/utils.py`
**Purpose:** Utility functions for the entire project

**What it does:**
- Sets up logging configuration
- Creates and manages directory structures
- Provides rate limiting decorators
- Implements retry logic for API calls
- Logs failed IDs for later retry
- Measures execution time

**Key functions:**
- `setup_logger(name, log_file)` - Configures logging
- `ensure_dir(path)` - Creates directories if needed
- `ensure_paper_folder(out_root, base_id)` - Creates paper-specific folders
- `rate_limited(min_interval_sec)` - Decorator for rate limiting
- `retry(max_tries, delay, backoff, exceptions)` - Decorator for retry logic
- `log_failed_id(file_path, base_id, reason)` - Logs failed papers
- `timeit(func)` - Decorator to measure execution time

---

#### `src/discovery.py`
**Purpose:** Discovery and validation of paper IDs (optional/auxiliary)

**What it does:**
- Generates ID ranges for crawling
- Checks if papers exist before processing
- Lists available versions for each paper
- Can be used standalone for pre-validation

**Key functions:**
- `id_range(start_id, end_id, year, month)` - Generates ID sequences
- `check_paper_exists(base_id, rate_limit)` - Validates paper existence
- `enumerate_ids_and_versions(...)` - Scans entire range

---

#### `src/requirements.txt`
**Purpose:** Python package dependencies

## Processing Pipeline

For each paper ID, the crawler executes these steps:

1. **ID Generation** (`main.py`)
   - Generates ID in format `yyyymm-nnnnn` (e.g., `202510-00824`)

2. **Download** (`downloader.py`)
   - Converts to API format `YYMM.NNNNN` (e.g., `2510.00824`)
   - Downloads all versions (v1, v2, ...) as `.tar.gz`
   - Saves to `tex/` directory

3. **Cleaning** (`cleaner.py`)
   - Extracts all `.tar.gz` archives
   - Removes image files (`.png`, `.jpg`, `.pdf`, etc.)
   - Strips figure environments from `.tex` files

4. **Metadata** (`metadata.py`)
   - Fetches metadata from arXiv API
   - Saves to `metadata.json`
   - Generates BibTeX citation in `references.bib`

5. **References** (`refs.py`)
   - Queries Semantic Scholar API
   - Extracts arXiv references
   - Saves to `references.json`

## Monitoring & Logging

The crawler provides detailed logging:

- **INFO**: Successful operations
- **WARNING**: Non-critical issues (e.g., missing v2)
- **ERROR**: Failed operations

Failed papers are logged to `failed_ids.txt` with reasons for later retry.

## Troubleshooting

### Connection Timeouts
**Solution:** The code has automatic retry logic. If persistent, check your internet connection.

### Resume After Interruption
**Solution:** Simply run the same command again. The crawler skips existing paper folders automatically.


## Expected Results

Based on test runs:
- **Success Rate:** 95-100%
- **Average Versions/Paper:** 1-2
- **Average References/Paper:** 20-40 (arXiv papers only)
- **Processing Time:** 3-5 seconds per paper
- **Total Runtime:** 5-6 hours for 5000 papers


## 👨‍💻 Student ID
20120187