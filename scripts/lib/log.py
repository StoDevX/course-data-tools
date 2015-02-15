import sys
import os

def log(*args):
	if not os.getenv('QUIET', False):
		print(*args, file=sys.stderr)

def log_err(*args):
	print(*args, file=sys.stderr)
