from bs4 import BeautifulSoup
import requests, os, csv, json, re
from googletrans import Translator

url = "https://www.ajsp.net/volume.php?vol=48#"
pdf_folder = "pdfs"
os.makedirs(pdf_folder, exist_ok=True)
source_name = "AJSP"
translator = Translator()

def clean_author(name):
    return re.sub(r"الباحث[\\\s]*", "", name).strip()

def is_arabic(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

r = requests.get(url)
r.raise_for_status()
soup = BeautifulSoup(r.text, "html.parser")

articles = []

for container in soup.find_all("div", class_="container"):
    title_ar = container.find("h2")
    title_en = container.find("h3")

    title_ar_text = title_ar.get_text(strip=True) if title_ar else ""
    title_en_text = title_en.get_text(strip=True) if title_en else ""

    # Gestion des titres
    if is_arabic(title_ar_text):
        title = title_ar_text
        title_en_final = title_en_text
        if not title_en_final:
            title_en_final = translator.translate(title, src='ar', dest='en').text
    else:
        title_en_final = title_en_text or title_ar_text
        title = translator.translate(title_en_final, src='en', dest='ar').text

    # Extraire auteurs
    authors_tags = container.find_all("a", class_="user_name")
    authors_list = [clean_author(a.get_text(strip=True)) for a in authors_tags]
    authors_json = json.dumps(authors_list, ensure_ascii=False)

    # PDF
    pdf_tag = container.find("a", href=lambda x: x and x.endswith(".pdf"))
    pdf_link = pdf_tag.get("href") if pdf_tag else ""
    pdf_path = ""
    if pdf_link:
        pdf_filename = pdf_link.split("/")[-1]
        pdf_path = os.path.join(pdf_folder, pdf_filename)
        try:
            r_pdf = requests.get(pdf_link)
            r_pdf.raise_for_status()
            with open(pdf_path, "wb") as f:
                f.write(r_pdf.content)
        except Exception as e:
            print(f"Erreur téléchargement {pdf_link}: {e}")
            pdf_path = ""

    articles.append({
        "title": title,
        "title_en": title_en_final,
        "authors": authors_json,
        "source": source_name,
        "path": pdf_path
    })

# CSV
csv_file = "articles.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["title","title_en","authors","source","path"], quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for art in articles:
        writer.writerow(art)

print(f"{len(articles)} articles extraits et CSV généré : {csv_file}")
