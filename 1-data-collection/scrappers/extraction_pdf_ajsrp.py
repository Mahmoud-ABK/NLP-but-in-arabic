import csv
import os
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
from googletrans import Translator

ARCHIVE_URL = "https://journals.ajsrp.com/index.php/ajsrp/en/issue/archive"
UA = {"User-Agent": "ajsrp-scraper/1.0 (+contact@example.com)"}
RATE_LIMIT = 0.6
OUTPUT_CSV = "ajsrp_articles.csv"
OUT_DIR = "ajsrp"

os.makedirs(OUT_DIR, exist_ok=True)

# ---------------- Translation ----------------
translator = Translator()
_translate_cache_ar = {}
_translate_cache_en = {}

def translate_to_ar(text: str) -> str:
    if not text:
        return ""
    if text in _translate_cache_ar:
        return _translate_cache_ar[text]
    try:
        ar = translator.translate(text, dest="ar").text
        _translate_cache_ar[text] = ar
        time.sleep(0.1)
        return ar
    except Exception:
        return text

def translate_to_en(text: str) -> str:
    if not text:
        return ""
    if text in _translate_cache_en:
        return _translate_cache_en[text]
    try:
        en = translator.translate(text, dest="en").text
        _translate_cache_en[text] = en
        time.sleep(0.1)
        return en
    except Exception:
        return text

# ---------------- HTTP session ----------------
def make_session():
    s = requests.Session()
    s.headers.update(UA)
    retries = Retry(
        total=4,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s

def get_soup(session, url):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml"), r.url

# ---------------- Helpers ----------------
def format_authors_for_csv(authors_list):
    quoted = [f'"{a}"' for a in authors_list if a]
    return "[" + ", ".join(quoted) + "]"

def filename_from_download_link(download_link: str) -> str:
    if not download_link:
        return ""
    path = urlparse(download_link).path.rstrip("/")
    parts = path.split("/")
    if "download" in parts:
        idx = parts.index("download") + 1
        tail = parts[idx:]
    else:
        tail = parts[-2:]
    base = "-".join([p for p in tail if p]) or "file"
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    base = base.replace("/", "-").replace("\\", "-")
    return base

# ---------------- Language detection ----------------
_AR_RANGES = (
    (0x0600, 0x06FF),
    (0x0750, 0x077F),
    (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF),
    (0xFE70, 0xFEFF),
    (0x0660, 0x0669),
)

def _is_arabic_char(ch: str) -> bool:
    cp = ord(ch)
    for a, b in _AR_RANGES:
        if a <= cp <= b:
            return True
    return False

def _is_latin_char(ch: str) -> bool:
    return ("A" <= ch <= "Z") or ("a" <= ch <= "z")

def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def clean_text(s: str) -> str:
    """
    Keep Arabic, Latin letters, digits, spaces, and selected punctuation:
    _ ' - . , ( ) / \
    """
    if not s:
        return ""
    # Allow Arabic, Latin, digits, spaces, and _ ' - . , ( ) / \
    allowed_pattern = (
        r"[^0-9A-Za-z\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF"
        r"\uFB50-\uFDFF\uFE70-\uFEFF\s_\-'\.,()/\\]"
    )
    return re.sub(allowed_pattern, "", s).strip()

def split_or_translate_title(raw_text: str) -> tuple[str, str]:
    """
    Returns (title_ar, title_en).
    If both scripts present: separate by character class.
    If only English: translate to Arabic.
    If only Arabic: translate to English.
    """
    text = (raw_text or "").strip()
    if not text:
        return ("", "")

    has_ar = any(_is_arabic_char(c) for c in text)
    has_en = any(_is_latin_char(c) for c in text)

    if has_ar and has_en:
        ar = "".join(c for c in text if _is_arabic_char(c) or c.isspace())
        en = "".join(c for c in text if _is_latin_char(c) or c.isspace() or c.isdigit())
        return (clean_text(_normalize_ws(ar)), clean_text(_normalize_ws(en)))

    if has_en:
        ar = translate_to_ar(text)
        return (clean_text(ar), clean_text(text))

    if has_ar:
        en = translate_to_en(text)
        return (clean_text(text), clean_text(en))

    ar = translate_to_ar(text)
    return (clean_text(ar), clean_text(text))

# ---------------- Scraping ----------------
def extract_issue_links(session, archive_url):
    soup, base = get_soup(session, archive_url)
    links = []
    for a in soup.select('h2 > a.title[href*="/issue/view/"]'):
        href = a.get("href", "").strip()
        if href:
            links.append(urljoin(base, href))
    seen, out = set(), []
    for u in links:
        if u not in seen:
            out.append(u); seen.add(u)
    return out

def extract_articles_from_issue(session, issue_url):
    soup, base = get_soup(session, issue_url)
    ul = soup.select_one("ul.cmp_article_list.articles")
    if not ul:
        return []

    items = ul.select(":scope > li")
    if len(items) <= 1:
        return []

    results = []
    for li in items[1:]:
        # ---- Title & Article URL ----
        a_title = li.select_one("h3.title a[href]")
        raw_title = a_title.get_text(strip=True) if a_title else ""
        article_url = urljoin(base, a_title["href"].strip()) if a_title and a_title.get("href") else ""

        # ---- Handle title detection/translation ----
        title_ar, title_en = split_or_translate_title(raw_title)

        # ---- Authors ----
        authors = [s.get_text(strip=True) for s in li.select("div.authors span.name")]
        authors_str = format_authors_for_csv(authors)

        # ---- PDF link ----
        a_pdf = li.select_one("ul.galleys_links a.obj_galley_link.pdf[href]")
        pdf_url = urljoin(base, a_pdf["href"].strip()) if a_pdf and a_pdf.get("href") else ""
        download_link = pdf_url.replace("/view/", "/download/") if pdf_url else ""

        # ---- Path ----
        file_name = filename_from_download_link(download_link) if download_link else ""
        path = f"./{OUT_DIR}/{file_name}" if file_name else ""

        if title_en or title_ar or authors or download_link or article_url:
            results.append({
                "title": title_ar,
                "title_en": title_en,
                "authors": authors_str,
                "source": "ajsrp",
                "path": path,
                "download_link": download_link,
                "article_url": article_url
            })
    return results

def main():
    session = make_session()
    issue_links = extract_issue_links(session, ARCHIVE_URL)
    print(f"# Found {len(issue_links)} issue page(s)\n")

    all_rows = []
    for i, issue in enumerate(issue_links, 1):
        print(f"## [{i}/{len(issue_links)}] {issue}")
        try:
            rows = extract_articles_from_issue(session, issue)
        except requests.HTTPError as e:
            print(f"   ! HTTP error on issue page: {e}")
            rows = []
        all_rows.extend(rows)
        time.sleep(RATE_LIMIT)

    fieldnames = ["title", "title_en", "authors", "source", "path", "download_link", "article_url"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n✅ Saved {len(all_rows)} rows to '{OUTPUT_CSV}'")

if __name__ == "__main__":
    main()
