#!/usr/bin/env python
# coding: utf-8

# # Step 2 : pages cleaning and preparation for extraction 

# In[1]:


import pandas as pd 
import numpy as np
import tqdm 
from utils.qwen import infer, getTokenCount
from utils.plots import boxplot_token_counts
tqdm.tqdm.pandas()


# In[2]:


df1=pd.read_csv("02-extracted-pages.csv")
df2=pd.read_csv("01-data.csv")


# ## now every article links to its path for verification later 

# In[3]:


df1["path"]=df2["path"]
data=df1.copy()
data.sample(1)


# ### now getting the token count for each page to see if it needs more cleaning

# In[4]:


data["page1_token_count"]=data["page1"].progress_apply(getTokenCount)
data["page2_token_count"]=data["page2"].progress_apply(getTokenCount)


# In[5]:


data['total_tokens']=data["page1_token_count"]+data["page2_token_count"]


# In[6]:


data.head(1)


# ### box plot to get token count for each page 

# In[7]:


boxplot_token_counts(data)


# ## Text contain so much ocr noise it needs to be cleaned 

# In[8]:


sample = data.sample(1).iloc[0]
print("page1 --------------: \n " + sample["page1"])
print("page2 --------------: \n " + sample["page2"])


# In[9]:


#This function normalises text , removes ocr noise and removes non arabic text blocs
from utils.preprocessing import clean_page


# In[10]:


print("page1 --------------: \n " + clean_page(sample["page1"]))
print("page2 --------------: \n " + clean_page(sample["page2"]))


# In[11]:


data["page1"] = data["page1"].progress_apply(clean_page)
data["page2"] = data["page2"].progress_apply(clean_page)


# ### Recalculate and replot

# In[12]:


data["page1_token_count"]=data["page1"].progress_apply(getTokenCount)
data["page2_token_count"]=data["page2"].progress_apply(getTokenCount)


# In[13]:


data['total_tokens']=data["page1_token_count"]+data["page2_token_count"]


# In[14]:


boxplot_token_counts(data)


# ### Conclusion : reduction in tokens further cleaning needed  

# #### let's remove rows whose totaltokens is less than (400 token ~ 200 words) 

# In[15]:


removed = (data["total_tokens"] < 400).sum()
data = data[data["total_tokens"] >= 400].reset_index(drop=True)

print("Rows removed:", removed)


# In[16]:


boxplot_token_counts(data)


# ### move non arabic names to authors_en
# 

# In[17]:


sample = data.iloc[40]
sample["authors"]


# In[18]:


from utils.preprocessing import move_non_arabic 
move_non_arabic(sample)


# In[19]:


data[["authors", "authors_en"]] = data.progress_apply(move_non_arabic, axis=1)


# In[20]:


columns_to_keep = [
    "article_id",
    "title",
    "abstract_ar",
    "authors",
    "authors_en",
    "general_field",
    "publish_date",
    "page1",
    "page2",
    "source",
    "path"
]

data = data[columns_to_keep].copy()
## add keywords for later
data["keywords"] = None


# In[21]:


data.to_csv("03-pages_cleaned.csv",index=False)

