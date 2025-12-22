#!/usr/bin/env python
# coding: utf-8

# In[12]:


import pandas as pd 


# In[13]:


authors=pd.read_csv("00-authors.csv")
articles=pd.read_csv("00-articles.csv")


# In[14]:


authors.info(),articles.info()


# In[15]:


def parse_string_to_list(s):
    """
    Parses a string like "['item1', 'item2']" into a Python list.
    Relies on basic string manipulation.
    """
    # Return an empty list if the input isn't a string or is empty
    if not isinstance(s, str) or not s:
        return []

    # 1. Remove the opening and closing square brackets
    content = s.strip().strip('[]')

    # If the content is empty after stripping brackets (was "[]" or " "), return empty list
    if not content:
        return []

    # 2. Split the string by commas
    items = content.split(',')

    # 3. Clean up each item by removing extra whitespace and quotes
    cleaned_items = [item.strip().strip("'\"") for item in items]

    return cleaned_items

# --- Apply this simple function ---
articles['keywords'] = articles['keywords'].apply(parse_string_to_list)
articles['author_ids'] = articles['author_ids'].apply(parse_string_to_list)
authors['articles_ids'] = authors['articles_ids'].apply(parse_string_to_list)

# --- Verification ---
print("Data types in 'articles' DataFrame after parsing:")
print(f"Type of 'keywords' in first row: {type(articles.loc[0, 'keywords'])}")
print(f"Type of 'keywords' in first row: {type(articles.loc[0, 'author_ids'])}")
print(f"Type of 'keywords' in first row: {type(authors.loc[0, 'articles_ids'])}")

# Display the head to show the result
articles.head()


# In[16]:


# Ensure keywords are strings and join them, then combine with the abstract.
# The .apply(lambda x: ' '.join(x)) handles the list of keywords correctly.
articles['combined_text'] = articles['abstract_ar'] + ' ' + articles['keywords'].apply(lambda x: ' '.join(map(str, x)))

# This column is now ready for AraBERT. No more processing is needed for the semantic path.
articles['text_for_bert'] = articles['combined_text']

print("Created 'combined_text' and 'text_for_bert' columns.")
articles[['abstract_ar', 'keywords', 'combined_text']].head()


# In[17]:


get_ipython().system('pip install Tashaphyne')


# In[18]:


# --- Step 2: Combine abstract and keywords ---
# The .join method creates a single string from the list of keywords.
# map(str, x) is a safeguard to ensure all items in the list are strings.
articles['combined_text'] = articles['abstract_ar'] + ' ' + articles['keywords'].apply(lambda x: ' '.join(map(str, x)))



from stemmer import remove_stopwords ,stem_text
# Apply the functions in the specified order: Stemming -> Stopword Removal
print("Processing text for TF-IDF...")
print("1. Applying light stemming...")
stemmed_text = articles['combined_text'].apply(stem_text)

print("2. Removing stopwords...")
articles['text_for_tfidf'] = stemmed_text.apply(remove_stopwords)
print("Processing complete.")


# --- Step 5: Verification ---
# Display the new columns to verify the results


# In[19]:


print("\nVerification of new text columns:")
articles[['combined_text', 'text_for_tfidf']].head()


# In[20]:


columns_to_save = [
    'article_id',
    'source',
    'path',
    'author_ids',
    'combined_text',  # Ready for AraBERT
    'text_for_tfidf'  # Ready for TF-IDF
]

# Ensure the columns exist before trying to save
existing_columns_to_save = [col for col in columns_to_save if col in articles.columns]

articles.to_csv('01-datatransformed.csv', 
                columns=existing_columns_to_save, 
                index=False,
                encoding='utf-8-sig') # 'utf-8-sig' is good for compatibility with Excel

print("Transformed data saved successfully to '00-datatransformed.csv'")


# In[ ]:




