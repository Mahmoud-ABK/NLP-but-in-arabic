#!/usr/bin/env python
# coding: utf-8

# In[63]:


import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split


# In[64]:


import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('01-datatransformed.csv')
authors = pd.read_csv("00-authors.csv")

# 1. Uniformize the Authors table IDs first
authors['id'] = authors['id'].astype(str).str.strip()

# 2. Improved parsing function to handle potential 'np.str_' literal text
def clean_id_list(s):
    if not isinstance(s, str) or not s or s == '[]': 
        return []

    # Remove brackets
    content = s.strip("[]")
    # Split by comma
    items = content.split(',')

    cleaned_items = []
    for item in items:
        # Remove whitespace and various types of quotes
        clean = item.strip().strip("'\"")
        # Remove literal "np.str_(" if it was accidentally saved into the CSV text
        clean = clean.replace("np.str_(", "").replace(")", "").strip("'\"")
        if clean:
            cleaned_items.append(str(clean)) # Force to standard Python string

    return cleaned_items

# 3. Apply cleaning to the main dataframe
df['author_ids'] = df['author_ids'].apply(clean_id_list)

# 4. Handle NaNs
df.fillna({'text_for_tfidf': ''}, inplace=True)

# 5. Re-split the data to ensure train/test sets are also clean
from sklearn.model_selection import train_test_split
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

print(f"Data Uniformed. Authors: {len(authors)}, Train: {len(train_df)}, Test: {len(test_df)}")


# In[65]:


train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

print(f"Training set shape: {train_df.shape}")
print(f"Testing set shape: {test_df.shape}")

# --- 3. Save the Splits to CSV ---
train_df.to_csv('02-train.csv', index=False, encoding='utf-8-sig')
test_df.to_csv('02-test.csv', index=False, encoding='utf-8-sig')


# In[66]:


import pandas as pd
import numpy as np
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Load the splits
train_df = pd.read_csv('02-train.csv')
test_df = pd.read_csv('02-test.csv')

# 2. Re-parse author_ids (since CSV saves lists as strings)
def parse_list(s):
    if not isinstance(s, str) or not s: return []
    return [item.strip().strip("'\"") for item in s.strip("[]").split(',')]

train_df['author_ids'] = train_df['author_ids'].apply(parse_list)
test_df['author_ids'] = test_df['author_ids'].apply(parse_list)

# 3. Fit TF-IDF on Training Data
# We use sublinear_tf to scale counts and min_df to ignore very rare typos
tfidf = TfidfVectorizer(sublinear_tf=True, min_df=2, ngram_range=(1, 1)) 
tfidf_matrix = tfidf.fit_transform(train_df['text_for_tfidf'].fillna(''))

print(f"Model fitted. Vocabulary size: {len(tfidf.vocabulary_)}")


# In[67]:


def recommend_reviewer_logic_verbose(query_text, k_depth=20):
    """
    Verbose implementation of Sequential Disambiguation logic.
    Provides a step-by-step trace of the recommendation process.
    """
    print("-" * 60)
    print("STARTING RECOMMENDATION PROCESS")
    print("-" * 60)

    # 1. Vectorize input
    query_vec = tfidf.transform([query_text])

    # 2. Calculate similarities
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()

    # 3. Get Top K indices
    top_indices = similarities.argsort()[::-1][:k_depth]

    # 4. STEP 1: Anchor Candidates
    best_match_idx = top_indices[0]
    best_score = similarities[best_match_idx]
    best_article_id = train_df.iloc[best_match_idx]['article_id']
    candidates = set(train_df.iloc[best_match_idx]['author_ids'])

    print(f"[STEP 1] ANCHOR MATCH FOUND")
    print(f"Nearest Article ID: {best_article_id}")
    print(f"Similarity Score:   {best_score:.4f}")
    print(f"Initial Candidates: {candidates}")

    # Safety check for zero similarity
    if best_score == 0:
        print("[ERROR] No similar articles found (Score is 0).")
        return None, None, "No Matches"

    # If article 1 has only one author, return immediately
    if len(candidates) == 1:
        winner = list(candidates)[0]
        print(f"[RESULT] Unique author found in nearest article. Selecting: {winner}")
        return winner, best_article_id, "Direct Match"

    # 5. STEP 2: Disambiguation Loop
    print(f"\n[STEP 2] DISAMBIGUATION (Tie between {len(candidates)} authors)")
    print(f"Scanning up to {k_depth} nearest matches for a tie-breaker...")

    for i in range(1, len(top_indices)):
        next_match_idx = top_indices[i]
        next_score = similarities[next_match_idx]
        next_id = train_df.iloc[next_match_idx]['article_id']
        next_authors = set(train_df.iloc[next_match_idx]['author_ids'])

        # Calculate intersection
        overlap = candidates.intersection(next_authors)

        print(f"\nRank {i+1} | Article {next_id} | Score: {next_score:.4f}")
        print(f"Article authors: {next_authors}")

        if len(overlap) == 0:
            print("No overlap with current candidates. Continuing...")
            continue

        elif len(overlap) == 1:
            winner = list(overlap)[0]
            print(f"[RESULT] Found unique tie-breaker at rank {i+1}")
            print(f"Winner identified: {winner}")
            print("-" * 60)
            return winner, best_article_id, f"Tie broken by rank {i+1}"

        else: # len(overlap) > 1
            print(f"Multiple candidates match ({overlap}). Narrowing candidate pool.")
            candidates = overlap

    # 6. STEP 3: Fallback
    print(f"\n[STEP 3] FALLBACK")
    print(f"Checked all {k_depth} articles. Tie persists between: {candidates}")
    winner = random.choice(list(candidates))
    print(f"Action: Randomly selecting from remaining candidates: {winner}")
    print("-" * 60)
    return str(winner), best_article_id, "Random Fallback (Tie)"


# In[68]:


def get_author_name(auth_id):
    if auth_id is None: 
        return "N/A"

    # Force search ID to string and strip any quotes
    search_id = str(auth_id).strip().strip("'\"")

    # Search in authors dataframe
    match = authors[authors['id'] == search_id]

    if not match.empty:
        return match.iloc[0]['name']
    else:
        # Debugging: if not found, let's see what the ID actually looks like
        return f"Unknown ({search_id})"


# In[79]:


# Pick a sample from test set
sample_row = test_df.sample(1).iloc[0]
query_text = sample_row['text_for_tfidf']
actual_ids = sample_row['author_ids']

# Run the inference (using the verbose function we wrote previously)
rec_id, match_article_id, method = recommend_reviewer_logic_verbose(query_text)

# Get Names
actual_names = [get_author_name(aid) for aid in actual_ids]
rec_name = get_author_name(rec_id)

print("\n" + "="*60)
print("FINAL INFERENCE SUMMARY")
print("-" * 60)
print(f"Actual Authors:      {actual_ids}")
print(f"Actual Names:        {', '.join(actual_names)}")
print("-" * 60)
print(f"Recommended ID:      {rec_id}")
print(f"Recommended Name:    {rec_name}")
print(f"Selection Method:    {method}")


# In[ ]:





# In[ ]:




