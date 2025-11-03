import arxiv, time, os

def _safe_download(paper, dirpath, filename, rate_limit):
    os.makedirs(dirpath, exist_ok=True)
    paper.download_source(dirpath=dirpath, filename=filename)
    time.sleep(1.0/max(rate_limit, 0.1))

def download_all_versions(base_id:str, paper_dir:str, rate_limit:float, workers:int):
    # Ví dụ đơn giản: thử v1..v10, dừng khi 404/không có
    versions = []
    client = arxiv.Client()
    for v in range(1, 11):
        vid = f"{base_id}v{v}"
        try:
            search = arxiv.Search(id_list=[vid])
            paper = next(client.results(search))
            _safe_download(paper, os.path.join(paper_dir, "tex"), f"{vid}.tar.gz", rate_limit)
            versions.append(vid)
        except StopIteration:
            break
    return versions
