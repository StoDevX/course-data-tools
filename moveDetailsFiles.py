from bs4 import BeautifulSoup
import os
data_path   = './'

def load_data_from_file(filename):
	with open(filename, 'r') as infile:
		content = infile.read()
		return content

def ensure_dir_exists(folder):
	# Make sure that a folder exists.
	d = os.path.dirname(folder)
	if not os.path.exists(d):
		os.makedirs(d)

def save_data(data, filepath):
	ensure_dir_exists(filepath)
	filename = os.path.split(filepath)[1]
	with open(filepath, mode='w+', newline='\n') as outfile:
		outfile.write(data)

	print('Wrote', filename, 'term data; %d bytes.' % (len(data)))


def find_details_subdir(clbid):
	n_thousand = int(int(clbid) / 1000)
	thousands_subdir = (n_thousand * 1000)
	return str(thousands_subdir).zfill(5) + '/' + str(clbid)

def get_details(padded_clbid):
	old_path = data_path + 'details/' + str(padded_clbid) + '.html'
	new_path = data_path + 'details/' + find_details_subdir(padded_clbid) + '.html'

	save_data(load_data_from_file(old_path), new_path)
	os.remove(old_path)

for filename in os.listdir('./details'):
	padded_clbid = os.path.splitext(os.path.basename(filename))[0]
	if padded_clbid != '.DS_Store':
		get_details(padded_clbid)
