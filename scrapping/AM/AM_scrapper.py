import os
import csv
import json
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import re

# -----------------------------
# Config
# -----------------------------
JOURNAL_URLS = [
    "https://journals.aabu.edu.jo/index.php/Art/issue/current",
    "https://journals.aabu.edu.jo/index.php/Edu/issue/current",
    "https://journals.aabu.edu.jo/index.php/Bus/issue/current"
]

DOWNLOAD_FOLDER = "pdf"  # PDFs folder relative to current script
OUTPUT_CSV = "AM_articles_scraped.csv"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# -----------------------------
# Helper functions
# -----------------------------
def clean_authors(name):
    """Remove Arabic word 'الباحث' and extra spaces from author names."""
    return re.sub(r"[\\\s]*الباحث[\\\s]*", "", name).strip()

# -----------------------------
# Scraping loop
# -----------------------------
articles = []
download_counter = 0

for base_url in JOURNAL_URLS:
    # Extract source suffix and prefix
    source_suffix = base_url.split("/")[-3]
    source_name = f"AM_{source_suffix}"  # e.g., AM_Art

    print(f"\nFetching {base_url} ...")
    response = requests.get(base_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Folder for this source
    source_folder = os.path.join(DOWNLOAD_FOLDER, source_suffix)
    os.makedirs(source_folder, exist_ok=True)

    for article_div in soup.find_all("div", class_="obj_article_summary"):
        download_counter += 1

        # ---- Titles ----
        title_en = ""
        title_ar = ""
        h3_tag = article_div.find("h3", class_="title")
        if h3_tag and h3_tag.find("a"):
            title_en = h3_tag.find("a").get_text(strip=True)
            try:
                title_ar = GoogleTranslator(source="en", target="ar").translate(title_en)
            except Exception:
                title_ar = title_en

        # ---- Authors ----
        authors = []
        authors_div = article_div.find("div", class_="authors")
        if authors_div:
            authors = [clean_authors(a.strip()) for a in authors_div.text.split(",")]

        # ---- PDF link ----
        pdf_tag = article_div.select_one("a.obj_galley_link.pdf")
        pdf_path = ""
        if pdf_tag:
            pdf_url = pdf_tag["href"]
            pdf_filename = f"{source_suffix}_{download_counter}.pdf"
            pdf_full_path = os.path.join(source_folder, pdf_filename)
            try:
                r_pdf = requests.get(pdf_url)
                r_pdf.raise_for_status()
                with open(pdf_full_path, "wb") as f:
                    f.write(r_pdf.content)
                # Save relative path for CSV
                pdf_path = os.path.relpath(pdf_full_path).replace("\\", "/")
                print(f"Downloaded PDF: {pdf_path}")
            except Exception as e:
                print(f"Error downloading PDF {pdf_url}: {e}")
                pdf_path = ""
        else:
            print(f"No PDF link found for article '{title_en}'")

        # ---- Append article data ----
        articles.append({
            "title": title_ar,
            "title_en": title_en,
            "authors": json.dumps(authors, ensure_ascii=False),
            "source": source_name,
            "path": pdf_path
        })

# -----------------------------
# Save CSV
# -----------------------------
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["title", "title_en", "authors", "source", "path"], quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(articles)

print(f"\n✅ Done. {len(articles)} articles saved to {OUTPUT_CSV}")
