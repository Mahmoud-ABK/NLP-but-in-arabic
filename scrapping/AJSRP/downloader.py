# save_as: download_from_csv.py
import csv
from pathlib import Path
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter, Retry

CSV_FILE = "ajsrp_articles.csv"   # change if needed
BASE_DIR = Path(".")              # base for relative paths in the CSV
HEADERS = {"User-Agent": "ajsrp-downloader/1.0 (+contact@example.com)"}

def make_session():
    s = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        raise_on_status=False,
    )
    s.headers.update(HEADERS)
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s

def download_file(session: requests.Session, url: str, out_path: Path):
    if not url:
        print("  ! missing download_link, skipping")
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        print(f"  = exists: {out_path}")
        return
    print(f"  ↓ {url} -> {out_path}")
    with session.get(url, stream=True, timeout=60) as r:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            print(f"  ! HTTP {r.status_code} for {url}: {e}")
            return
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

def main():
    session = make_session()
    rows = 0
    downloaded = 0

    with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += 1
            download_link = (row.get("download_link") or "").strip()
            path_str = (row.get("path") or "").strip()

            if not path_str:
                # fallback filename if 'path' is empty
                # derive from URL last two segments (e.g., /download/9161/8053 -> 9161-8053.pdf)
                p = urlparse(download_link).path.rstrip("/").split("/")
                tail = "-".join(p[-2:]) + ".pdf" if len(p) >= 2 else "file.pdf"
                path_str = f"./ajsrp/{tail}"

            out_path = BASE_DIR / Path(path_str)

            download_file(session, download_link, out_path)
            downloaded += 1

    print(f"\nDone. Processed rows: {rows}. Attempted downloads: {downloaded}.")

if __name__ == "__main__":
    main()
