#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# In[26]:


from utils.qwen import extract_article_metadata 
import pandas as pd
import tqdm
tqdm.tqdm.pandas()


# In[3]:


data = pd.read_csv("03-pages_cleaned.csv")


# In[5]:


data.head(1)


# ### expermient with sample 

# In[6]:


sample = data.sample(1).iloc[0]


# In[7]:


type(sample)


# In[8]:


sample[["article_id","path"]]


# In[9]:


page1,page2 = sample["page1"] ,sample["page2"]


# In[10]:


from IPython.display import HTML, display

display(HTML(f"""
<div dir="rtl" style="text-align: right; font-size: 16px;">
page1 <br>
{page1}
<br>
page2 <br>
{page2}
<br>
</div>
"""))


# In[11]:


json=extract_article_metadata(page1,page2)


# In[12]:


from IPython.display import HTML, display

display(HTML(f"""
<div dir="rtl" style="text-align: right; font-size: 16px;">
{json}
</div>
"""))


# In[13]:


json.keys() 


# In[14]:


sample.keys()


# ## process row function

# In[17]:


# this is a  function that takes a row and returns a new row processed 
from utils.processing import process_row

processed = process_row(sample)


# In[23]:


display(HTML(f"""
<div dir="rtl" style="text-align: right; font-size: 16px;">
{processed.to_dict()}
</div>
"""))


# ### now we need just to parallelise it 

# In[80]:


# let's get a csv sample tp simulate processing 
subset = data.sample(2)
subset


# In[81]:


subset = subset.progress_apply(process_row,axis=1)


# In[36]:


subset


# ### Names also need a normalisation process but not now 

# In[79]:


subset.to_csv("sample.csv")


# In[ ]:




