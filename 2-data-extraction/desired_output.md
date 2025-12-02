# Article Schema — Field Descriptions
- article_id  
  A unique identifier for the article (e.g., UUID or file hash) used to join, reference, and deduplicate records.
- title  
  The article’s title exactly as published (string).
- abstract_ar  
  The article’s abstract in Arabic (original text).
- general field  
  The subject area or classification label for the article (e.g., "economics", "literature").
- field 
  more specific than general field 
- authors  
  The ordered list of author names (e.g., semicolon-separated string or JSON array).
- publish_date  
  The publication date in ISO 8601 format (YYYY-MM-DD); null if unknown.

-authors_en
- abstract_en  
  The article’s abstract in English (human or machine translation). If machine-translated, record that fact (e.g., in a note or flag).
-title_en