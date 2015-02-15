from .ensure_dir_exists import ensure_dir_exists
import os

def save_data(data, filepath):
	ensure_dir_exists(filepath)
	filename = os.path.split(filepath)[1]
	with open(filepath, mode='w+', newline='\n') as outfile:
		outfile.write(data)
