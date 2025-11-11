def addARPD():
	import glob
	full_path = os.path.join(os.path.dirname(__file__), 'fullarticles.csv')
	header = FULLARTICLES_COLUMNS
	full_dir = os.path.dirname(full_path)
	# Find all files under ARPD (recursively)
	arpd_dir = os.path.join(os.path.dirname(__file__), 'ARPD')
	file_paths = [y for x in os.walk(arpd_dir) for y in [os.path.join(x[0], f) for f in x[2]]]
	new_rows = []
	for abs_path in file_paths:
		rel_path = os.path.relpath(abs_path, full_dir)
		# Extract field from path (the first folder under ARPD)
		parts = rel_path.split(os.sep)
		try:
			arpd_index = parts.index('ARPD')
			field = parts[arpd_index + 1] if len(parts) > arpd_index + 1 else ''
		except ValueError:
			field = ''
		row = ['' for _ in header]
		if 'source' in header:
			row[header.index('source')] = 'ARPD'
		if 'path' in header:
			row[header.index('path')] = rel_path
		if 'general_field' in header:
			row[header.index('general_field')] = field
		new_rows.append(row)
	with open(full_path, 'a', newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		writer.writerows(new_rows)
def addAJSP():
	ajsp_path = os.path.join(os.path.dirname(__file__), 'AJSP', 'articles .csv')
	full_path = os.path.join(os.path.dirname(__file__), 'fullarticles.csv')
	header = FULLARTICLES_COLUMNS
	with open(ajsp_path, newline='', encoding='utf-8') as f:
		ajsp_reader = csv.DictReader(f)
		ajsp_rows = list(ajsp_reader)
	full_dir = os.path.dirname(full_path)
	new_rows = []
	for row in ajsp_rows:
		new_row = []
		for col in header:
			val = row.get(col, '')
			if col == 'path' and val:
				abs_path = os.path.normpath(os.path.join(os.path.dirname(ajsp_path), val))
				rel_path = os.path.relpath(abs_path, full_dir)
				val = rel_path
			new_row.append(val)
		new_rows.append(new_row)
	with open(full_path, 'a', newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		writer.writerows(new_rows)

def addAJSRP():
	ajsrp_path = os.path.join(os.path.dirname(__file__), 'AJSRP', 'ajsrp_articles.csv')
	full_path = os.path.join(os.path.dirname(__file__), 'fullarticles.csv')
	header = FULLARTICLES_COLUMNS
	with open(ajsrp_path, newline='', encoding='utf-8') as f:
		ajsrp_reader = csv.DictReader(f)
		ajsrp_rows = list(ajsrp_reader)
	full_dir = os.path.dirname(full_path)
	new_rows = []
	for row in ajsrp_rows:
		new_row = []
		for col in header:
			val = row.get(col, '')
			if col == 'path' and val:
				abs_path = os.path.normpath(os.path.join(os.path.dirname(ajsrp_path), val))
				rel_path = os.path.relpath(abs_path, full_dir)
				val = rel_path
			new_row.append(val)
		new_rows.append(new_row)
	with open(full_path, 'a', newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		writer.writerows(new_rows)

def addAM():
	am_path = os.path.join(os.path.dirname(__file__), 'AM', 'AM_articles_scraped.csv')
	full_path = os.path.join(os.path.dirname(__file__), 'fullarticles.csv')
	header = FULLARTICLES_COLUMNS
	with open(am_path, newline='', encoding='utf-8') as f:
		am_reader = csv.DictReader(f)
		am_rows = list(am_reader)
	full_dir = os.path.dirname(full_path)
	new_rows = []
	for row in am_rows:
		new_row = []
		for col in header:
			val = row.get(col, '')
			if col == 'path' and val:
				abs_path = os.path.normpath(os.path.join(os.path.dirname(am_path), val))
				rel_path = os.path.relpath(abs_path, full_dir)
				val = rel_path
			new_row.append(val)
		new_rows.append(new_row)
	with open(full_path, 'a', newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		writer.writerows(new_rows)
# Columns for each CSV file
AJP_COLUMNS = ['title', 'title_en', 'authors', 'source', 'path']
AJSP_COLUMNS = ['title', 'title_en', 'authors', 'source', 'path']
AJSRP_COLUMNS = ['title', 'title_en', 'authors', 'source', 'path', 'download_link', 'article_url']
AM_COLUMNS = ['title', 'title_en', 'authors', 'source', 'path']
import csv
import os

FULLARTICLES_COLUMNS = [
	'article_id', 'title', 'title_en', 'abstract_ar', 'abstract_en', 'general_field', 'field',
	'authors', 'authors_en', 'publish_date', 'references', 'raw_content', 'content', 'appendices', 'source', 'path'
]


def addAJP():
	ajp_path = os.path.join(os.path.dirname(__file__), 'AJP', 'scraped_articles.csv')
	full_path = os.path.join(os.path.dirname(__file__), 'fullarticles.csv')

	# Use the global FULLARTICLES_COLUMNS list
	header = FULLARTICLES_COLUMNS

	# Read AJP csv
	with open(ajp_path, newline='', encoding='utf-8') as f:
		ajp_reader = csv.DictReader(f)
		ajp_rows = list(ajp_reader)

	# Prepare rows to append
	new_rows = []
	full_dir = os.path.dirname(full_path)
	for row in ajp_rows:
		new_row = []
		for col in header:
			val = row.get(col, '')
			if col == 'path' and val:
				# Make path relative to fullarticles.csv
				abs_path = os.path.normpath(os.path.join(os.path.dirname(ajp_path), val))
				rel_path = os.path.relpath(abs_path, full_dir)
				val = rel_path
			new_row.append(val)
		new_rows.append(new_row)

	# Append to fullarticles.csv
	with open(full_path, 'a', newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		writer.writerows(new_rows)
# Post-process AM rows in fullarticles.csv to fill general_field from path
def fill_general_field_for_AM():
    full_path = os.path.join(os.path.dirname(__file__), 'fullarticles.csv')
    header = FULLARTICLES_COLUMNS
    full_dir = os.path.dirname(full_path)
    rows = []
    with open(full_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    # If header is present in file, skip it
    if rows and rows[0] == header:
        data_rows = rows[1:]
    else:
        data_rows = rows
    updated_rows = []
    for row in data_rows:
        if len(row) < len(header):
            row += [''] * (len(header) - len(row))
        if 'source' in header and row[header.index('source')] == 'AM':
            path_val = row[header.index('path')]
            parts = path_val.split(os.sep)
            try:
                am_index = parts.index('AM')
                field = parts[am_index + 1] if len(parts) > am_index + 1 else ''
            except ValueError:
                field = ''
            row[header.index('general_field')] = field
        updated_rows.append(row)
    # Write back (without header)
    with open(full_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(updated_rows)


if __name__ == '__main__':
	fill_general_field_for_AM()
    
