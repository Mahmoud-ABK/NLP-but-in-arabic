#!/usr/bin/env python
# coding: utf-8

# In[6]:


import pandas as pd 
import os


# In[2]:


data=pd.read_csv("03-pages_cleaned.csv")


# In[4]:


data.info()


# In[7]:


output_dir = "./metadata-extraction/"
os.makedirs(output_dir, exist_ok=True)

chunk_size = 200
num_chunks = (len(data) + chunk_size - 1) // chunk_size  # ceiling division

for i in range(num_chunks):
    start = i * chunk_size
    end = start + chunk_size
    chunk = data.iloc[start:end]

    chunk_path = os.path.join(output_dir, f"chunk_{i}.csv")
    chunk.to_csv(chunk_path, index=False)

    print(f"Saved {chunk_path}")


# In[ ]:




