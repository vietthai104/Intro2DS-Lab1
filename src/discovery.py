"""
discovery.py
-------------
Module dùng để sinh dải ID arXiv và kiểm tra paper nào tồn tại,
đồng thời liệt kê số version của từng paper.

Yêu cầu:
- Input: start_id, end_id, year, month
- Output: list các base_id (vd: '202510-00824') có tồn tại trên arXiv
- Optional: kiểm tra version (v1..vn)
"""

import arxiv
import time
import tqdm
import logging

# Thiết lập logger cơ bản
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


def id_range(start_id: int, end_id: int, year: int, month: int):
    """
    Sinh chuỗi ID dạng yyyymm-id (5 chữ số).
    Ví dụ: id_range(824, 827, 2025, 10)
    → ["202510-00824", "202510-00825", "202510-00826", "202510-00827"]
    """
    for i in range(start_id, end_id + 1):
        yield f"{year}{month:02d}-{i:05d}"


def check_paper_exists(base_id: str, rate_limit: float = 1.0):
    """
    Kiểm tra xem paper có tồn tại hay không trên arXiv.
    Nếu có, trả về danh sách version (v1, v2, ...).
    Nếu không, trả về [].
    """
    client = arxiv.Client()
    versions = []

    # arxiv ID dạng '202510.00824', cần chuyển từ '202510-00824'
    api_id = base_id.replace("-", ".")

    for v in range(1, 11):
        vid = f"{api_id}v{v}"
        try:
            search = arxiv.Search(id_list=[vid])
            paper = next(client.results(search))
            versions.append(f"{base_id}v{v}")
            time.sleep(1.0 / max(rate_limit, 0.1))
        except StopIteration:
            # không có version này nữa => dừng
            break
        except Exception as e:
            logging.warning(f"Error checking {vid}: {e}")
            time.sleep(2)
    return versions


def enumerate_ids_and_versions(start_id: int, end_id: int, year: int, month: int, rate_limit: float = 1.0):
    """
    Hàm chính: duyệt toàn bộ dải ID, kiểm tra paper nào tồn tại.
    Trả về dict: {base_id: [v1, v2, ...]}
    """
    all_papers = {}
    total = end_id - start_id + 1
    logging.info(f"Checking {total} IDs from {year}-{month:02d}")

    for base_id in tqdm.tqdm(id_range(start_id, end_id, year, month), total=total):
        versions = check_paper_exists(base_id, rate_limit)
        if versions:
            all_papers[base_id] = versions
            logging.info(f"Found {base_id}: {len(versions)} version(s)")
        else:
            logging.debug(f"Not found: {base_id}")

    logging.info(f"Total found: {len(all_papers)} papers")
    return all_papers


if __name__ == "__main__":
    # Test nhanh khi chạy file riêng
    found = enumerate_ids_and_versions(1000, 1003, 2025, 10, rate_limit=1.0)
    for k, v in found.items():
        print(k, "=>", v)
