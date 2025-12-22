#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')
import pandas as pd
# Use tqdm.auto to automatically detect if you are in a notebook or terminal
from tqdm.auto import tqdm 
import os
from utils.processing import process_row


# In[2]:


# Configuration
input_folder = "metadata-extraction-input"
output_folder = "metadata-extraction-output"
os.makedirs(output_folder, exist_ok=True)


# In[4]:


# 3,4,5
for i in range(3,6):
    input_filename = f"chunk_{i}.csv"
    input_path = os.path.join(input_folder, input_filename)
    output_path = os.path.join(output_folder, f"chunk_{i}_processed.csv")

    if not os.path.exists(input_path):
        print(f"File {input_filename} not found, skipping.")
        continue

    # 1. Load the input data
    df = pd.read_csv(input_path)

    # 2. Resume logic: Check how many rows are already processed
    start_idx = 0
    if os.path.exists(output_path):
        try:
            # We read only the index/header to count rows quickly
            existing_df = pd.read_csv(output_path)
            start_idx = len(existing_df)
        except (pd.errors.EmptyDataError, Exception):
            start_idx = 0

    if start_idx >= len(df):
        print(f"Chunk {i} is already fully processed.")
        continue

    print(f"Processing {input_filename} starting from row {start_idx}...")

    # 3. Process remaining rows
    # We use a standard loop with tqdm for manual row-by-row control
    remaining_rows = df.iloc[start_idx:]

    for idx, row in tqdm(remaining_rows.iterrows(), total=len(remaining_rows), desc=f"Chunk {i}"):
        # Process the single row
        processed_data = process_row(row,6001,"51.75.140.143")

        # Convert the result to a DataFrame (1 row)
        # If process_row returns a Series, use .to_frame().T
        # If it returns a dict, use pd.DataFrame([processed_data])
        if isinstance(processed_data, pd.Series):
            res_df = processed_data.to_frame().T
        else:
            res_df = pd.DataFrame([processed_data])

        # Append to CSV
        # header=True only if the file is being created for the first time
        res_df.to_csv(
            output_path, 
            mode='a', 
            index=False, 
            header=not os.path.exists(output_path) or os.stat(output_path).st_size == 0
        )


# In[ ]:




