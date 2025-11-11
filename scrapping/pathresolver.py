#!/usr/bin/env python3
import csv
import os
import sys

def is_relative_and_exists(base_dir, rel_path):
    if os.path.isabs(rel_path):
        return False
    abs_path = os.path.normpath(os.path.join(base_dir, rel_path))
    return os.path.exists(abs_path)

def check_csv(csv_path):
    base_dir = os.path.dirname(csv_path)
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        invalid = []
        for i, row in enumerate(reader, 2):
            path = row.get('path', '')
            if not path or not is_relative_and_exists(base_dir, path):
                invalid.append((i, path))
    if invalid:
        print(f'File: {csv_path}')
        print('Invalid or non-relative paths:')
        for line, path in invalid:
            print(f'  Line {line}: {path}')
    else:
        print(f'File: {csv_path}')
        print('All paths are valid and relative to the CSV file.')

def main():
    scrapping_dir = os.path.abspath(os.path.dirname(__file__))
    for root, dirs, files in os.walk(scrapping_dir):
        for file in files:
            if file.endswith('.csv'):
                check_csv(os.path.join(root, file))

if __name__ == '__main__':
    main()
