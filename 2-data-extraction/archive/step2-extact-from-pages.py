#!/usr/bin/env python
# coding: utf-8

# # Step 2 : using models to extract data

# ##

# ## test on one row

# In[1]:


import pandas as pd 
from utils.qwen import infer, getTokenCount , extract_article_metadata
import tqdm
tqdm.tqdm.pandas()
import json
import re


# ## starting with getting token counts

# In[2]:


data = pd.read_csv("1-step1.csv")


# 

# In[3]:


getTokenCount(data.loc[0, "page1"])


# In[4]:


getTokenCount(data.loc[0, "page2"])


# In[5]:


getTokenCount(data.loc[0, "page3"])


# ### Lets get the average token count to adjust the model parameters

# In[6]:


data[[f"{page}_token_count" for page in ["page1", "page2", "page3"]] ] = data[["page1", "page2", "page3"]].progress_apply(lambda x: [getTokenCount(x["page1"]), getTokenCount(x["page2"]), getTokenCount(x["page3"])], axis=1, result_type='expand')


# In[7]:


data.head(2)


# In[8]:


import matplotlib.pyplot as plt

plt.figure(figsize=(8, 6))
box = plt.boxplot(
    [data['page1_token_count'], data['page2_token_count'], data['page3_token_count']],
    labels=['page1', 'page2', 'page3'],
    patch_artist=True,
    showmeans=True
)

# Annotate median, mean, min, max for each box
for i, column in enumerate(['page1_token_count', 'page2_token_count', 'page3_token_count']):
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


# ### lets remove non arabic letters and unecessary spaces to reduce token counts 

# In[9]:


before_cleaning = data.copy()


# In[10]:


# Define a regex pattern to keep Arabic letters, numbers, and punctuations
arabic_pattern = r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9.,;:!?()\[\]{}\-–—\'"“”\s]'

for page in ['page1', 'page2', 'page3']:
    data[page] = data[page].apply(lambda x: re.sub(arabic_pattern, '', x))


# In[11]:


for page in ['page1', 'page2', 'page3']:
    data[page] = data[page].apply(lambda x: re.sub(r'\s+', ' ', x).strip())


# ### Recalculate

# In[12]:


data[[f"{page}_token_count" for page in ["page1", "page2", "page3"]] ] = data[["page1", "page2", "page3"]].progress_apply(lambda x: [getTokenCount(x["page1"]), getTokenCount(x["page2"]), getTokenCount(x["page3"])], axis=1, result_type='expand')


# In[13]:


import matplotlib.pyplot as plt

plt.figure(figsize=(8, 6))
box = plt.boxplot(
    [data['page1_token_count'], data['page2_token_count'], data['page3_token_count']],
    labels=['page1', 'page2', 'page3'],
    patch_artist=True,
    showmeans=True
)

# Annotate median, mean, min, max for each box
for i, column in enumerate(['page1_token_count', 'page2_token_count', 'page3_token_count']):
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


# ### we reduced token counts and now the we can infere qwen proprely for good performance
# 

# In[14]:


data.to_csv("2-step2.csv", index=False)


# In[22]:


print(data['page2'][30])  


# ### let's try now the inference for extraction

# In[16]:


import pprint 

res = extract_article_metadata([data.loc[0, "page1"], data.loc[0, "page2"]],6000)


# In[17]:


res


# In[ ]:




