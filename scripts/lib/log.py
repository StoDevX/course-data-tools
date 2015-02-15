import sys
import os

def log(*args, **kwargs):
	if not os.getenv('QUIET', False):
		print(*args, **kwargs, file=sys.stderr)

def log_err(*args, **kwargs):
	print(*args, **kwargs, file=sys.stderr)
