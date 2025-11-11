import csv
import os
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, parse_qs

def scrape_and_download(input_csv_path, output_csv_path, download_folder_base):
    """
    Scrapes websites from an input CSV, downloads PDFs with unique names, 
    and writes extracted data to an output CSV.
    """
    scraped_data = []
    download_counter = 0

    with open(input_csv_path, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            url = row['url']
            acronym = row['acronym']
            
            download_folder = os.path.join(download_folder_base, acronym)
            if not os.path.exists(download_folder):
                os.makedirs(download_folder)

            print(f"Scraping {url}...")
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching {url}: {e}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            
            for doc_div in soup.find_all('div', class_='doc'):
                pdf_link_tag = doc_div.select_one('p.pdf a')
                if not pdf_link_tag or not pdf_link_tag.get('href'):
                    continue
                pdf_url = pdf_link_tag.get('href')

                title, title_en = "", ""
                title_link_tag = doc_div.select_one('p:not(.pdf) a')
                if title_link_tag:
                    full_title_text = title_link_tag.text.strip()
                    if ". " in full_title_text:
                        parts = full_title_text.split('. ', 1)
                        title = parts[0] + '.'
                        title_en = parts[1]
                    else:
                        title = full_title_text

                authors = []
                authors_span = doc_div.find('span', class_='auth')
                if authors_span:
                    authors = [author.strip() for author in authors_span.text.split(' and ')]

                try:
                    download_counter += 1
                    parsed_url = urlparse(pdf_url)
                    query_params = parse_qs(parsed_url.query)
                    article_number = query_params.get('article', [f'unk{download_counter}'])[0]

                    # STEP 1: Define a local filename with the .pdf extension.
                    # This is how we ensure the file is recognized as a PDF on your computer.
                    pdf_filename = f"{acronym}_{article_number}_{download_counter}.pdf"
                    pdf_path = os.path.join(download_folder, pdf_filename)
                    
                    print(f"  Downloading from CGI script {pdf_url} to {pdf_path}")
                    
                    # STEP 2: Request the content from the CGI script. 
                    # The server sends back the binary data of the PDF.
                    pdf_response = requests.get(pdf_url)
                    pdf_response.raise_for_status()
                    
                    # STEP 3: Write the received binary data into your local .pdf file.
                    # 'wb' mode is important here, as it means "write bytes".
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_response.content)

                    scraped_data.append({
                        'title': title,
                        'title_en': title_en,
                        'authors': json.dumps(authors, ensure_ascii=False),
                        'source': acronym,
                        'path': pdf_path
                    })

                except requests.exceptions.RequestException as e:
                    print(f"  Error downloading {pdf_url}: {e}")
                    continue

    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as outfile:
        fieldnames = ['title', 'title_en', 'authors', 'source', 'path']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(scraped_data)

    print(f"\nScraping complete. Data saved to {output_csv_path}")

if __name__ == '__main__':
    INPUT_CSV = 'toscrap.csv'
    OUTPUT_CSV = 'scraped_articles.csv'
    DOWNLOAD_FOLDER = '/home/mahmoud/Engineering/isimm/ing2/data-treatment/scrapping/pdf/'
    
    scrape_and_download(INPUT_CSV, OUTPUT_CSV, DOWNLOAD_FOLDER)
