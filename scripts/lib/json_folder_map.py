from .parse_year_from_filename import parse_year_from_filename
from collections import OrderedDict
import hashlib
import json
import os

def json_folder_map(folder, kind, quiet=True):
	output = {
		'files': [],
		'type': kind
	}

	files = os.listdir(folder)
	for filename in files:
		if filename == '.DS_Store':
			continue
		path = folder + '/' + filename
		with open(path, 'rb') as infile:
			info = {
				'path': 'terms/' + filename,
				'hash': hashlib.sha1(infile.read()).hexdigest(),
				'year': parse_year_from_filename(filename)
			}
			output['files'].append(OrderedDict(sorted(info.items())))

	output['files'] = sorted(output['files'], key=lambda item: item['path'])

	output = OrderedDict(sorted(output.items()))

	if not dry_run:
		with open(info_path, 'w') as outfile:
			outfile.write(json.dumps(output, indent='\t', separators=(',', ': ')))
			outfile.write('\n')

	if not quiet: print('Hashed files; wrote info.json')
