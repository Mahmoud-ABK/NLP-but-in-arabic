#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pytesseract
from pdf2image import convert_from_path


# In[2]:


PDF_PATH = "ex1.pdf"
OUTPUT_PATH = "ex1.txt"


# In[3]:


# OCR both Arabic and English
LANG = "ara+eng"

# Convert PDF pages to images
pages = convert_from_path(PDF_PATH, dpi=300)


# In[6]:


from tqdm import tqdm

text = ""

for i, page in enumerate(tqdm(pages, desc="Extracting text", unit="page"), start=1):
    page_text = pytesseract.image_to_string(page, lang=LANG)
    text += f"\n{page_text}\n"
# Save to file
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(text)


# In[7]:


print(f"""OCR done! Mixed Arabic–English text extracted to  {OUTPUT_PATH}""")


# In[ ]:




