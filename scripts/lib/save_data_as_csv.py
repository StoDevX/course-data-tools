import csv
import os

def save_data_as_csv(data, filepath):
	ensure_dir_exists(filepath)
	filename = os.path.split(filepath)[1]
	with open(filepath, 'w+') as outfile:
		csv_file = csv.DictWriter(outfile, data[0].keys())
		csv_file.writeheader()
		csv_file.writerows(data)

	if not quiet: print('Wrote', filename, 'term data; %d bytes.' % (len(data)))
