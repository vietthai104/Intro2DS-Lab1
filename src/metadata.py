import json, arxiv
from datetime import datetime
import os

def _to_iso(dt):  # convert datetime to ISO date string
    if isinstance(dt, datetime): return dt.date().isoformat()
    return str(dt)

def write_metadata_json(base_id, paper_dir, versions):
    client = arxiv.Client()
    # Lấy metadata từ version mới nhất (nếu cần bạn có thể hợp nhất)
    search = arxiv.Search(id_list=[versions[-1] if versions else base_id])
    paper = next(client.results(search))
    data = {
        "title": paper.title,
        "authors": [a.name for a in paper.authors],
        "submission_date": _to_iso(paper.published),
        "revised_dates": [_to_iso(paper.updated)] if paper.updated else [],
        "venue": paper.journal_ref or None,
        "versions": versions
    }
    with open(os.path.join(paper_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_bibtex(base_id, paper_dir):
    # cách nhanh: dựng bibtex tối thiểu từ metadata; hoặc gọi endpoint bibtex của arXiv
    bib = f"""@misc{{arXiv:{base_id},
  title={{...}},
  author={{...}},
  howpublished={{arXiv preprint arXiv:{base_id}}},
  year={{...}}
}}"""
    open(os.path.join(paper_dir, "references.bib"), "w", encoding="utf-8").write(bib)
