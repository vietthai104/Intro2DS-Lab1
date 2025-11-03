import requests, time, os, json

def fetch_and_write_references(base_id, paper_dir, rate_limit=1.0):
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{base_id}"
    params = {"fields": "references,references.externalIds,references.title,references.authors,references.year"}
    r = requests.get(url, params=params, timeout=30)
    time.sleep(1.0/max(rate_limit, 0.1))
    refs = {}
    if r.ok:
        data = r.json()
        for ref in (data.get("references") or []):
            ext = (ref.get("externalIds") or {})
            arx = ext.get("ArXiv")
            if arx:
                # chuyển "YYMM.NNNNN" → "yyyymm-id" (đủ 4 số năm-tháng nếu cần)
                yymm, nnnnn = arx.split(".")
                y = "20" + yymm[:2] if len(yymm)==4 else yymm[:4]
                m = yymm[-2:]
                key = f"{y}{m}-{nnnnn}"
                authors = [a.get("name") for a in (ref.get("authors") or []) if a.get("name")]
                refs[key] = {
                    "title": ref.get("title"),
                    "authors": authors,
                    "submission_date": None,   # không có -> để None hoặc tìm thêm
                    "revised_dates": []
                }
    with open(os.path.join(paper_dir, "references.json"), "w", encoding="utf-8") as f:
        json.dump(refs, f, ensure_ascii=False, indent=2)
