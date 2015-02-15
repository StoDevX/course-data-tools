from argparse import ArgumentParser
import functools
import xmltodict
import requests
import json

from .load_data_from_file import load_data_from_file
from .save_data_as_csv import save_data_as_csv
from .fix_invalid_xml import fix_invalid_xml
from .paths import make_xml_term_path
from .delete_file import delete_file
from .save_data import save_data
from .log import log, log_err


def request_term_from_server(term):
	# Yes, the request needs all of these extra parameters in order to run.
	url = 'http://www.stolaf.edu/sis/public-acl-inez.cfm?searchyearterm=' \
		+ str(term) \
		+ '&searchkeywords=&searchdepts=&searchgereqs=&searchopenonly=off&' \
		+ 'searchlabonly=off&searchfsnum=&searchtimeblock='

	request = requests.get(url)

	if 'Sorry, there\'s been an error.' in request.text:
		log_err('Error in', url, '\nWhoops! Made another error in the server.')
		if 'The request has exceeded the allowable time limit' in request.text:
			log_err('And that error is exceeding the time limit. Again.\nWe should probably do something about that.')

		return

	return request.text


def ensure_list_in_term(xml_term_data):
	# If there is only one course for a semester, then raw_term_data
	# is just an object; otherwise, it's a list. We need to ensure that
	# it is always a list.
	if xml_term_data['searchresults']:
		if type(xml_term_data['searchresults']['course']) is not list:
			xml_term_data['searchresults']['course'] = [xml_term_data['searchresults']['course']]
		xml_term_data['searchresults']['course'] = sorted(xml_term_data['searchresults']['course'], key=lambda c: c['clbid'])
	return xml_term_data


def embed_term_in_courses(xml_term_data, term):
	for course in xml_term_data['searchresults']['course']:
		course['term'] = term
	return xml_term_data


def load_data_from_server(term, dry_run=False):
	xml_term_path = make_xml_term_path(term)

	raw_data = request_term_from_server(term)
	valid_data = fix_invalid_xml(raw_data)
	xmldict = xmltodict.parse(valid_data)

	parsed_data = ensure_list_in_term(xmldict)

	if not parsed_data['searchresults']:
		log('No data returned for', term)
		return None

	embedded_terms = embed_term_in_courses(parsed_data, term)

	if not dry_run:
		reparsed_data = xmltodict.unparse(embedded_terms, pretty=True)
		save_data(reparsed_data, xml_term_path)
		log('Fetched', xml_term_path)

	return embedded_terms


def load_term(term, force_download=False, dry_run=False):
	xml_term_path = make_xml_term_path(term)
	data = ''

	if not force_download:
		try:
			# log('Loading', term, 'from disk')
			raw_data = load_data_from_file(xml_term_path)
			data = xmltodict.parse(raw_data)
		except FileNotFoundError:
			log('Requesting', term, 'from server')
			data = load_data_from_server(term, dry_run=dry_run)
	else:
		log('Forced to request', term, 'from server')
		data = load_data_from_server(term, dry_run=dry_run)

	return data


if __name__ == '__main__':
	argparser = ArgumentParser()
	argparser.add_argument('term', type=int)
	argparser.add_argument('--force-download', '-f', action='store_true')
	argparser.add_argument('--dry-run', '-d', action='store_true')
	args = argparser.parse_args()

	data = load_term(**vars(args))

	courses = data['searchresults']['course']
	[print(course['clbid']) for course in courses]
