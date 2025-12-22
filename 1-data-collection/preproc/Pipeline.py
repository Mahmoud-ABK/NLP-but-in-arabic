#!/usr/bin/env python
# coding: utf-8

# # Import the text

# In[24]:


content=""
with open("ex1.txt", "r", encoding="utf-8") as file:
    content = file.read()
    print(content)


# ## Import list

# In[54]:


import re # step 2 3 4 
import regex # step 1 2
import emoji # step 2

from pyarabic.araby import strip_tashkeel, strip_tatweel  # step5


import nltk # step 6 

# Download tokenizer models
nltk.download('punkt')

from nltk.stem.isri import ISRIStemmer # step 6 
from nltk.tokenize import word_tokenize # step 6 

import arabicstopwords.arabicstopwords as stp #step 7


# ## Step 1: Remove Non-Arabic Content
# - Remove English letters
# - Remove numbers

# In[33]:


step1 = regex.sub(r'[\p{Latin}\d]+', '', content)


# ## Step 2: Remove Punctuation
# - Remove English punctuation marks
# - Remove Arabic punctuation marks
# - remove invisible and emojis etc...

# In[34]:


def clean_text(text):

    text = emoji.replace_emoji(text, replace='')

    #Remove all punctuation (any Unicode punctuation)
    text = regex.sub(r'[\p{P}\p{S}]+', '', text)


    invisible_chars = r'[\u200e\u200f\u200b\u200c\u200d\u2060]'
    text = regex.sub(invisible_chars, '', text)

    return text

# Usage
step2 = clean_text(step1)


# In[35]:


step2


# ## Step 3: Clean Whitespace
# - Replace multiple spaces with a single space
# - Trim leading and trailing spaces
# - temove \t and \n and other spacing stuff

# In[36]:


# Replace multiple spaces, tabs, newlines, and other whitespace with a single space
step3 = re.sub(r'\s+', ' ', step2)

# Trim leading and trailing spaces
step3 = step3.strip()


# In[38]:


step3


# In[39]:


# check point save to text 
with open("steps/step3.txt", "w", encoding="utf-8") as f:
    f.write(step3)


# ## Step 4: Remove Diacritics
# - Remove all Arabic diacritical marks (tashkeel)
# - Remove tatwil/kashida

# In[40]:


step4 = strip_tashkeel(step3)
step4 = strip_tatweel(step4)


# ## Step 5: Normalize Characters
# - Normalize Alef variations to standard Alef
# - Normalize Yaa variations to standard Yaa
# - Normalize Taa Marbuta to Haa marbuta

# In[41]:


def normalize_arabic(text):
    """
    Normalize Arabic characters:
    - Alef variations (أ، إ، آ) → ا
    - Yaa variations (ى, ئ) → ي
    - Taa Marbuta (ة) → ه (Haa Marbuta)
    """
    # Normalize Alef
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')

    # Normalize Yaa
    text = text.replace('ى', 'ي').replace('ئ', 'ي')

    # Normalize Taa Marbuta
    text = text.replace('ة', 'ه')

    return text


# In[42]:


step5 = normalize_arabic(step4)


# In[51]:


step5


# ## Step 6: Stemming/Lemmatization and Tokenization
# - Reduce words to their root form

# In[46]:


def tokenize_and_stem(text):
    # Tokenize text into words
    tokens = word_tokenize(text)

    # Initialize Arabic stemmer
    stemmer = ISRIStemmer()

    # Stem each token
    stemmed_tokens = [stemmer.stem(token) for token in tokens]

    return stemmed_tokens


# In[47]:


step6 = tokenize_and_stem(step5)


# In[48]:


step6


# ## Step 7: Remove Stopwords
# - Filter out Stopwords

# In[52]:


def remove_stopwords(tokens):
    """
    Remove Arabic stopwords from a list of tokens
    """
    stopwords = set(stp.stopwords_list())
    filtered_tokens = [token for token in tokens if token not in stopwords]
    return filtered_tokens


# In[55]:


step7 = remove_stopwords(step6)


# In[56]:


step7


# In[57]:


with open("steps/step7_tokens.txt", "w", encoding="utf-8") as f:
    for token in step7:
        f.write(token + "\n")


# In[ ]:




