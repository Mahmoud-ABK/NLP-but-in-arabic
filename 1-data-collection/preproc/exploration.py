#!/usr/bin/env python
# coding: utf-8

# # Exploration de pyarabic.araby

# In[1]:


from pyarabic.araby import strip_tashkeel, strip_tatweel,TASHKEEL,TATWEEL


# In[2]:


TASHKEEL


# In[3]:


TATWEEL


# In[4]:


get_ipython().run_line_magic('pinfo2', 'strip_tashkeel')


# In[6]:


get_ipython().run_line_magic('pinfo2', 'strip_tatweel')


# # Exploration de arabicstopwords

# In[15]:


import arabicstopwords.arabicstopwords as stp #more range of arabic stop words


# In[16]:


stp.STOPWORDS


# In[ ]:




