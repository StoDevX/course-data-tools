from .log import log
from .ensure_dir_exists import ensure_dir_exists
from .get_all_keys import get_all_keys
import csv
import os

def save_data_as_csv(data, filepath):
	ensure_dir_exists(filepath)
	filename = os.path.split(filepath)[1]
	for item in data:
		if 'revisions' in item:
			item.pop('revisions')
		for key in item:
			if type(item[key]) is str:
				item[key] = item[key].replace('\n','\\n')
	with open(filepath, 'w', newline='') as outfile:
		csv_file = csv.DictWriter(outfile, get_all_keys(data))
		csv_file.writeheader()
		csv_file.writerows(data)

	log('Wrote', filename, 'term data; %d bytes.' % (len(data)))
