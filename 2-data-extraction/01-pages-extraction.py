#!/usr/bin/env python
# coding: utf-8

# # Pages extraction

# In[1]:


import pandas as pd 
import numpy as np
import tqdm 
tqdm.tqdm.pandas()


# In[3]:


raw = pd.read_csv("00-raw.csv")


# In[4]:


raw.info()


# In[5]:


raw.head()


# removing some abnormalities in authors columns

# In[6]:


data = raw.copy()


# In[7]:


data["authors"] = data["authors"].str.replace("1","")
data["authors"] = data["authors"].str.replace(",2","")
data["authors"] = data["authors"].str.replace("*","")
data["authors"] = data["authors"].str.replace("&",",")
data["authors"] = data["authors"].str.replace("/",",")
data["authors"] = data["authors"].str.replace("\u200c","")


# In[8]:


data["authors"].tolist()


# In[9]:


data.isnull().sum()


# In[10]:


data.to_csv('01-data.csv', index=False)


# # Step 1 Extracting Necessary Pages

# ## Test for one pdf

# In[11]:


from utils.firstpages import extract_first_three_pages , extract_first_two_pages_ocr

extract_first_two_pages_ocr(data['path'][20])


# ## Extract pages

# In[12]:


batch_size = 100  
num_batches = int(np.ceil(len(data) / batch_size))

for batch_idx in range(num_batches):
    start_idx = batch_idx * batch_size
    end_idx = min((batch_idx + 1) * batch_size, len(data))
    batch = data.iloc[start_idx:end_idx]
    if 'path' in batch.columns:
        pages = batch['path'].progress_apply(extract_first_two_pages_ocr).tolist()
        data.loc[batch.index, ['page1', 'page2']] = pd.DataFrame(pages, index=batch.index)
        data.to_csv(f"step1_progress_batch_{batch_idx}.csv", index=False)

if 'path' in data.columns:
    data = data.drop(columns=["path"])


# In[14]:


data.to_csv('02-extracted-pages.csv', index=False)


# In[ ]:


import re

def clean_page_text(text):
    # Remove all unicode control characters except \n and regular spaces
    # Remove unnecessary spaces (multiple spaces to single space, strip leading/trailing)
    if not isinstance(text, str):
        return text
    # Remove unicode control characters except \n and space
    text = re.sub(r'[^\S\r\n ]+', '', text)
    # Replace multiple spaces with a single space
    text = re.sub(r' +', ' ', text)
    # Strip leading/trailing spaces
    text = text.strip()
    return text

for col in ['page1', 'page2']:
    data[col] = data[col].apply(clean_page_text)


# In[ ]:


def remove_decorative_punctuations(text):
    if not isinstance(text, str):
        return text
    # Remove common decorative punctuations and repeated dots
    text = re.sub(r'[•●▪♦■★☆※…—–―–‐‑⁃⁄⁎⁑⁂⁕⁖⁗⁘⁙⁚⁛⁜⁝⁞]', '', text)
    text = re.sub(r'[.]{3,}', '.', text)  # Replace 3 or more consecutive dots with a single dot
    text = re.sub(r'[_~^`]+', '', text)  # Remove underscores, tildes, etc.
    text = re.sub(r'[“”‘’]', '', text)   # Remove fancy quotes
    text = re.sub(r'[=]+', '', text)     # Remove repeated equals
    text = re.sub(r'[\u2022-\u2023\u25A0-\u25FF]', '', text)  # Remove unicode bullets/squares
    return text.strip()

for col in ['page1', 'page2']:
    data[col] = data[col].apply(remove_decorative_punctuations)


# In[23]:


data.head(2)


# In[24]:


data.to_csv('1-step1.csv', index=False)


# In[ ]:




