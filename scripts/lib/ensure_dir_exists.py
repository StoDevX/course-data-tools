import os

def ensure_dir_exists(folder):
	# Make sure that a folder exists.
	d = os.path.dirname(folder)
	os.makedirs(d, exist_ok=True)
