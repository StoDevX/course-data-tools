import json

from .log import log
from .save_data import save_data
from .paths import make_built_term_path
from .save_data_as_csv import save_data_as_csv

def save_term(term_data, path, kind):
	if not term_data:
		return

	term = term_data[0]['term']

	term_path = make_built_term_path(term, kind, path + 'terms/')
	log('saving term', term, 'to', term_path)
	if kind == 'json':
		json_term_data = json.dumps(term_data, indent='\t', separators=(',', ': '), sort_keys=True) + '\n'
		save_data(json_term_data, term_path)
	elif kind == 'csv':
		save_data_as_csv(term_data, term_path)
