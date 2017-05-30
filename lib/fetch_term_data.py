import xmltodict
import requests
import re

from .load_data_from_file import load_data_from_file
from .paths import make_xml_term_path
from .save_data import save_data
import logging


def fix_invalid_xml(raw):
    # Replace any invalid XML entities with &amp;
    subst = '&amp;'
    cleaned = re.sub(r'&(?!(?:[a-z]+|#[0-9]+|#x[0-9a-f]+);)', subst, raw)
    return cleaned


def request_term_from_server(term):
    url = 'http://www.stolaf.edu/sis/static-classlab/{}.xml'.format(term)

    try:
        request = requests.get(url, timeout=60)
    except requests.exceptions.Timeout as ex:
        logging.warning('Timeout requesting {}'.format(url))
        return None

    if 'Sorry, there\'s been an error.' in request.text:
        logging.warning('Error in the request for {}'.format(url))
        logging.warning('Whoops! Made another error in the server.')
        if 'The request has exceeded the allowable time limit' in request.text:
            logging.warning('We exceeded the server\'s internal time limit for the request.')
        else:
            logging.warning('{}'.format(request.text))

        return None

    return request.text


def embed_term_in_courses(xml_term_data, term):
    for course in xml_term_data['searchresults']['course']:
        course['term'] = term
    return xml_term_data


def load_data_from_server(term, dry_run=False):
    xml_term_path = make_xml_term_path(term)

    raw_data = request_term_from_server(term)
    if not raw_data:
        logging.info('No data returned for {}'.format(term))
        return None

    valid_data = fix_invalid_xml(raw_data)
    parsed_data = xmltodict.parse(valid_data, force_list=['course',])

    if not parsed_data['searchresults']:
        logging.info('No data returned for {}'.format(term))
        return None

    # We sort the courses here, before we save it to disk, so that we don't
    # need to re-sort every time we load from disk.
    parsed_data['searchresults']['course'].sort(key=lambda c: c['clbid'])

    embedded_terms = embed_term_in_courses(parsed_data, term)

    if not dry_run:
        reparsed_data = xmltodict.unparse(embedded_terms, pretty=True)
        save_data(reparsed_data, xml_term_path)
        logging.debug('Fetched {}'.format(xml_term_path))

    return embedded_terms


def load_term(term, force_download=False, dry_run=False):
    xml_term_path = make_xml_term_path(term)

    if not force_download:
        try:
            logging.info('Loading {} from disk'.format(term))
            with open(xml_term_path, 'rb') as infile:
                data = xmltodict.parse(infile, force_list=['course',])
        except FileNotFoundError:
            logging.info('Requesting {} from server'.format(term))
            data = load_data_from_server(term, dry_run=dry_run)
    else:
        logging.info('Forced to request {} from server'.format(term))
        data = load_data_from_server(term, dry_run=dry_run)

    if data:
        for course in data['searchresults']['course']:
            yield course
