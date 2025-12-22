#!/usr/bin/env python
# coding: utf-8

# # Heuristic Approach 

# In[2]:


get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# In[3]:


import pandas as pd
import re
import numpy as np
from tqdm import tqdm
tqdm.pandas()


# In[4]:


data = pd.read_csv("03-pages_cleaned.csv")
# Ensure text columns are strings
data['page1'] = data['page1'].astype(str)
data['page2'] = data['page2'].astype(str)


# ## Define Heuristic Logic
# We define Regex patterns to capture:
# 1. **Abstract**
# 2. **Keywords**

# In[5]:


from utils.preprocessing import extract_abstract ,extract_keywords


# ### Apply Extraction

# In[6]:


# 1. Extract Abstract
data['abstract_ar'] = data.progress_apply(extract_abstract, axis=1)

# 2. Extract Keywords
data['keywords'] = data.progress_apply(extract_keywords, axis=1)


# In[7]:


data.head()


# In[8]:


data.head(1)["page1"].iloc[0]


# In[9]:


from utils.various import arabic_print
sample = data.sample(1).iloc[0]
abstarct,kws,page1,page2 = sample["abstract_ar"] ,sample["keywords"],sample["page1"],sample["page2"]
arabic_print("abstarct",abstarct,"kws",kws,"pages",page1,page2)


# ### Clean and Fill Data
# Since this is a heuristic approach, some abstracts might be missing. We will fill missing abstracts with a placeholder to ensure the dataset structure remains valid for subsequent processing steps.

# In[10]:


print(data["abstract_ar"].isnull().sum())
print(data["keywords"].isnull().sum())


# In[11]:


# Drop rows where "abstract_ar" or "keywords" are NaN
data = data.dropna(subset=["abstract_ar", "keywords"])

# Verify the changes
print(f"Nulls in abstract_ar: {data['abstract_ar'].isnull().sum()}")
print(f"Nulls in keywords: {data['keywords'].isnull().sum()}")


# In[16]:


# List of columns to keep
columns_to_keep = [
    'article_id', 'authors', 'authors_en', 
    'abstract_ar', 'source', 'path', 'keywords'
]

# Overwrite the dataframe with only these columns
data = data[columns_to_keep]


# In[17]:


data.to_csv("05-heuristic_extraction.csv", index=False)


# In[ ]:





# In[ ]:




