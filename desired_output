# Article Schema — Field Descriptions

- article_id  
  A unique identifier for the article (e.g., UUID or file hash) used to join, reference, and deduplicate records.

- title  
  The article’s title exactly as published (string).
-title_en 
- abstract_ar  
  The article’s abstract in Arabic (original text).

- abstract_en  
  The article’s abstract in English (human or machine translation). If machine-translated, record that fact (e.g., in a note or flag).

- field  
  The subject area or classification label for the article (e.g., "economics", "literature").

- authors  
  The ordered list of author names (e.g., semicolon-separated string or JSON array).
-authors_en
- publish_date  
  The publication date in ISO 8601 format (YYYY-MM-DD); null if unknown.

- references  
  The article’s reference list as raw citation strings or a JSON array of citations.

- raw_content  
  The article text exactly as extracted from the source (raw OCR/text dump), including front matter, headers/footers, page numbers, captions, references, acknowledgments, and any pre/post material.

- content  
  The cleaned main body text only (raw_content trimmed to remove front/back matter such as cover page, headers/footers, page numbers, table of contents, references, acknowledgments, and anything outside the main article body), ready for NLP processing.

- appendices  
  Any appendix or supplementary material text extracted from the article (raw/unprocessed), including labeled appendices, supplementary notes, and additional tables/figures that appear after the main content.

- source  
  Provenance information: original URL, repository name, or local file path where the file was obtained.
