import json

from .log import log
from .save_data import save_data
from .paths import make_json_term_path

def save_term(term_data):
	if not term_data:
		return

	term = term_data[0]['term']
	term_path = make_json_term_path(term)
	log('saving term', term, 'to', term_path)
	json_term_data = json.dumps(term_data, indent='\t', separators=(',', ': '), sort_keys=True) + '\n'
	save_data(json_term_data, term_path)
