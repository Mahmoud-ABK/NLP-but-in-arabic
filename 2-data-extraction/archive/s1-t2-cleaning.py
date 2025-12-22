#!/usr/bin/env python
# coding: utf-8

# # the goal of this is to reduce as much as we can the token counts for the model

# In[7]:


import pandas as pd 
import numpy as np
import tqdm 
from utils.qwen import infer, getTokenCount
tqdm.tqdm.pandas()


# In[5]:


data=pd.read_csv("02-extracted-pages.csv")


# In[6]:


data.head(2)


# In[10]:


data[[f"{page}_token_count" for page in ["page1", "page2"]] ] = data[["page1", "page2"]].progress_apply(lambda x: [getTokenCount(x["page1"]), getTokenCount(x["page2"])], axis=1, result_type='expand')


# In[12]:


import matplotlib.pyplot as plt

plt.figure(figsize=(8, 6))
box = plt.boxplot(
    [data['page1_token_count'], data['page2_token_count']],
    labels=['page1', 'page2'],
    patch_artist=True,
    showmeans=True
)

# Annotate median, mean, min, max for each box
for i, column in enumerate(['page1_token_count', 'page2_token_count']):
    col_data = data[column].dropna()
    median = col_data.median()
    mean = col_data.mean()
    min_val = col_data.min()
    max_val = col_data.max()
    plt.text(i + 1, median, f'Median: {median:.0f}', ha='center', va='bottom', fontsize=9, color='blue')
    plt.text(i + 1, mean, f'Mean: {mean:.0f}', ha='center', va='top', fontsize=9, color='red')
    plt.text(i + 1, min_val, f'Min: {min_val:.0f}', ha='center', va='top', fontsize=8, color='green')
    plt.text(i + 1, max_val, f'Max: {max_val:.0f}', ha='center', va='bottom', fontsize=8, color='purple')

plt.ylabel('Token Count')
plt.title('Boxplot of Token Counts for Each Page')
plt.show()


# In[13]:


data.head(1)


# In[ ]:




