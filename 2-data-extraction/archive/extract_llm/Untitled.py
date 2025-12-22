#!/usr/bin/env python
# coding: utf-8

# In[5]:


from workflow import work


# In[7]:


work()


# In[8]:


import pandas as pd


# In[10]:


a=pd.read_csv("03-extracted-pages-with-tokens.filled.csv")


# In[11]:


a["abstract_ar"][1]


# In[12]:


a["title"][1]


# In[ ]:




