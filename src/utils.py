"""
utils.py
---------
Các hàm tiện ích chung cho toàn project Arxiv Data Crawler:
- Tạo thư mục lưu output
- Ghi log, thông báo lỗi
- Rate-limit & retry helper
- Ghi danh sách ID lỗi
"""

import os
import time
import logging
from functools import wraps

# =======================
# 🧱 CẤU HÌNH LOG MẶC ĐỊNH
# =======================
def setup_logger(name: str = "crawler", log_file: str = "crawler.log"):
    """
    Thiết lập logger chung.
    Dùng logger riêng cho từng module nếu muốn (vd: utils.get_logger(__name__))
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ======================
# 📁 FILESYSTEM UTILITIES
# ======================
def ensure_dir(path: str):
    """
    Đảm bảo thư mục tồn tại. Nếu chưa có thì tạo.
    Trả về path để tiện chain function.
    """
    os.makedirs(path, exist_ok=True)
    return path


def ensure_paper_folder(out_root: str, base_id: str):
    """
    Tạo thư mục riêng cho mỗi paper: <out_root>/<base_id>/
    Bên trong tạo sẵn tex/ nếu chưa có.
    """
    paper_dir = os.path.join(out_root, base_id)
    tex_dir = os.path.join(paper_dir, "tex")
    os.makedirs(tex_dir, exist_ok=True)
    return paper_dir


# =====================
# 🕒 RATE LIMITER DECORATOR
# =====================
def rate_limited(min_interval_sec=1.0):
    """
    Decorator đảm bảo mỗi lần gọi cách nhau ít nhất min_interval_sec giây.
    Dùng để tránh bị block khi gọi API arXiv / Semantic Scholar.
    """
    def decorator(func):
        last_call = [0.0]

        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < min_interval_sec:
                time.sleep(min_interval_sec - elapsed)
            result = func(*args, **kwargs)
            last_call[0] = time.time()
            return result
        return wrapper

    return decorator


# ======================
# 🔁 RETRY HELPER (EXPO BACKOFF)
# ======================
def retry(max_tries=3, delay=1.0, backoff=2.0, exceptions=(Exception,)):
    """
    Decorator retry khi gặp lỗi.
    Dùng cho các hàm tải hoặc gọi API có thể timeout / fail tạm thời.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _delay = delay
            for attempt in range(1, max_tries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_tries:
                        raise
                    logging.warning(f"⚠️ Retry {attempt}/{max_tries} after error: {e}")
                    time.sleep(_delay)
                    _delay *= backoff
        return wrapper
    return decorator


# ======================
# ❌ GHI ID LỖI
# ======================
def log_failed_id(file_path: str, base_id: str, reason: str = ""):
    """
    Ghi ID bị lỗi vào file để có thể retry sau.
    """
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"{base_id}\t{reason}\n")


# ======================
# ⏱️ ĐO THỜI GIAN THỰC THI
# ======================
def timeit(func):
    """
    Decorator để đo thời gian thực thi hàm.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logging.info(f"⏱️ {func.__name__} finished in {end - start:.2f}s")
        return result
    return wrapper


# ======================
# 🧪 TEST NHANH
# ======================
if __name__ == "__main__":
    logger = setup_logger()
    logger.info("🔧 utils.py ready to use.")
    ensure_dir("test_folder")
    ensure_paper_folder("OUTPUT", "202510-00824")
    log_failed_id("failed_ids.txt", "202510-00824", "Test error")
    print("✅ Everything ok.")
