#!/usr/bin/env python
# coding: utf-8

# # Author Augmentation & Normalization
# 
# **Goal:** Create a consistent Author-Article Graph.
# 
# **Methodology:**
# 1. **Preservation:** Extract valid authors from the heuristic extraction results. Normalize names (remove titles, standardize formats) and assign unique IDs. These links are preserved exactly as found.
# 2. **Augmentation:** For articles missing author metadata (empty fields), we impute authors by sampling from the identified pool of real authors.
# 3. **Statistical Targets:**
#    - **Authors per Article:** Target mean of $\approx 1.5$.
#    - **Articles per Author:** Target mean of $\approx 5.0$ (adjusted by available pool size).

# In[21]:


get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# In[22]:


import pandas as pd
import re
import numpy as np
import ast
from tqdm import tqdm

tqdm.pandas()


# In[23]:


# Load Data
data = pd.read_csv("05-heuristic_extraction.csv")

# Ensure list columns are parsed correctly from strings
def safe_eval(x):
    try:
        if pd.isna(x): return []
        val = ast.literal_eval(x)
        if isinstance(val, list): return val
        return []
    except:
        return []

data['authors_list_ar'] = data['authors'].apply(safe_eval)
data['authors_list_en'] = data['authors_en'].apply(safe_eval)


# ## Name Normalization
# Standardizing author names by removing academic titles (Dr., Prof., etc.) and special characters to ensure unique entity resolution.

# In[24]:


def clean_author_name(name):
    if not isinstance(name, str):
        return None

    name = name.strip()

    # --- Arabic Cleanups ---
    # Remove titles like د. (Dr), أ. (Prof/Mr), م. (Eng), etc.
    name = re.sub(r'^\s*(أ\.د\.|أ\. د\.|د\.|أ\.|م\.|الاستاذ|الدكتور|الباحث|الطالب|الشيخ)\s+', '', name)
    # Remove non-name characters (digits, brackets)
    name = re.sub(r'[_\*\(\)\[\]\d]', '', name)

    # --- English Cleanups ---
    name = re.sub(r'^\s*(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.|Eng\.|PhD)\s+', '', name, flags=re.IGNORECASE)

    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()

    # Filter out garbage (too short)
    if len(name) < 3:
        return None

    return name


# ## Indexing Existing Authors
# 
# We iterate through the dataset to build a registry of real authors found in the extraction phase. These authors are assigned persistent IDs.

# In[25]:


# Registry: Name -> ID
author_registry = {}
next_auth_id = 1

# List to store the IDs for each article (preserving order)
article_author_ids = []

for idx, row in tqdm(data.iterrows(), total=len(data)):
    raw_authors = row['authors_list_ar'] + row['authors_list_en']

    current_ids = []

    if raw_authors:
        for raw_name in raw_authors:
            clean_name = clean_author_name(raw_name)
            if clean_name:
                # Register new author if not found
                if clean_name not in author_registry:
                    author_registry[clean_name] = f"AUTH_{next_auth_id:05d}"
                    next_auth_id += 1

                current_ids.append(author_registry[clean_name])

        # Deduplicate authors within the same article
        current_ids = list(set(current_ids))

    article_author_ids.append(current_ids)

data['author_ids'] = article_author_ids

print(f"Total Unique Authors Extracted: {len(author_registry)}")

# Create pool for sampling
all_author_ids_pool = list(author_registry.values())


# ## Imputing Missing Data
# 
# Articles with no extracted authors are filled using the existing author pool. 
# The distribution of authors per article is weighted to achieve a mean of $\approx 1.5$.
# 
# **Distribution Weights:**
# - 1 Author: 60%
# - 2 Authors: 30%
# - 3 Authors: 8%
# - 4 Authors: 2%

# In[26]:


np.random.seed(42)

# Weighted probabilities to target ~1.5 authors/article
probs = [0.60, 0.30, 0.08, 0.02]

def fill_empty_authors(ids_list):
    # PRESERVE existing data
    if len(ids_list) > 0:
        return ids_list

    # FILL missing data from pool
    if not all_author_ids_pool:
        return []

    k = np.random.choice([1, 2, 3, 4], p=probs)
    chosen = np.random.choice(all_author_ids_pool, size=k, replace=False)
    return list(chosen)

data['author_ids'] = data['author_ids'].apply(fill_empty_authors)


# ## Statistical Aggregation

# In[27]:


# 1. Create ID -> Name Map
id_to_name = {v: k for k, v in author_registry.items()}

# 2. Explode (Article -> AuthorID) to (AuthorID -> Article)
exploded = data[['article_id', 'author_ids']].explode('author_ids')
exploded = exploded.dropna(subset=['author_ids'])

# 3. Group by Author
authors_stats = exploded.groupby('author_ids').agg(
    articles_count=('article_id', 'count'),
    articles_ids=('article_id', list)
).reset_index()

# 4. Attach Names
authors_stats['name'] = authors_stats['author_ids'].map(id_to_name)
authors_stats.rename(columns={'author_ids': 'id'}, inplace=True)

authors_stats = authors_stats[['id', 'name', 'articles_count', 'articles_ids']]

print("--- Statistics ---")
mean_authors_per_article = data['author_ids'].apply(len).mean()
mean_articles_per_author = authors_stats['articles_count'].mean()

print(f"Mean Authors per Article: {mean_authors_per_article:.2f}")
print(f"Mean Articles per Author: {mean_articles_per_author:.2f}")
print("\n--- Top 5 Authors ---")
authors_stats.sort_values(by='articles_count', ascending=False).head()


# ## Output Generation

# In[28]:


authors_stats.describe()


# In[36]:


final_data.head()


# In[37]:


final_data["author_count"]=final_data["author_ids"].apply(len)
final_data["author_count"].describe()


# In[40]:


final_data.columns


# In[41]:


# Save Authors Database
authors_stats.to_csv("06-authors.csv", index=False)

# Save Enriched Dataset
# Retaining core columns and the new ID linkages
final_cols = [c for c in data.columns if c not in ['authors', 'authors_en', 'authors_list_ar', 'authors_list_en']]
final_data = data[final_cols]

final_data.to_csv("06-data-extraction-final.csv", index=False)

print("Process Complete. Files saved.")


# In[ ]:




