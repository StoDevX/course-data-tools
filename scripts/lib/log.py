import sys
import os

def log(*args, **kwargs):
	if not os.getenv('QUIET', False):
		print(*args, file=sys.stderr, **kwargs)

def log_err(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)
