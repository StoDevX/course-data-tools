import xmltodict
import requests
import urllib.parse
import re
import logging

from .paths import make_xml_term_path
from .save_data import save_data


class BadDataException(Exception):
    pass


def fix_invalid_xml(raw):
    """Replace any invalid XML entities with &amp;"""
    return re.sub(r'&(?!(?:[a-z]+|#[0-9]+|#x[0-9a-f]+);)', '&amp;', raw)


def build_term_url(term):
    base_url = 'https://www.stolaf.edu/sis/public-acl-inez.cfm'
    # Yes, the request needs all of these extra parameters in order to run.
    querystring = urllib.parse.urlencode({'searchyearterm': str(term)})
    return f'{base_url}?{querystring}'


def build_static_term_url(term):
    return f'https://sis.stolaf.edu/sis/static-classlab/{term}.xml'


def request_from_server(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
    except requests.exceptions.Timeout:
        logging.warning(f'Timeout requesting {url}')
        return None
    except requests.HTTPError as err:
        if err.response.status_code == 404:
            raise err
        if "Sorry, there's been an error." in err.response.text:
            logging.warning('Whoops! Made another error in the server:')
            logging.warning(f'{r.text}')
        if 'The request has exceeded the allowable time limit' in err.response.text:
            logging.warning("We exceeded the server's internal time limit for the request.")
        raise err

    return r.text


def request_data(url, term):
    raw_data = request_from_server(url)
    if not raw_data:
        logging.info(f'No data returned for {term}')
        return None

    try:
        # remove the coldfusion debugging output
        end = '</searchresults>'
        end_idx = raw_data.index(end) + len(end)
        raw_data = raw_data[:end_idx]
    except ValueError:
        raise BadDataException(f'{term} did not return any xml')

    # remove invalid xml entities
    valid_data = fix_invalid_xml(raw_data)

    # Parse the data into an actual data structure
    return xmltodict.parse(valid_data, force_list=['course'])


def load_data_from_server(term, dry_run=False):
    try:
        url = build_static_term_url(term)
        parsed_data = request_data(url, term)
    except BadDataException:
        print(f'{term}: static file is invlid xml; attempting database query')
        url = build_term_url(term)
        try:
            parsed_data = request_data(url, term)
        except BadDataException:
            print(f'{term}: fetching attempt #1 failed')
            try:
                parsed_data = request_data(url, term)
            except BadDataException:
                print(f'{term}: fetching attempt #2 failed')
                try:
                    parsed_data = request_data(url, term)
                except BadDataException:
                    print(f'{term}: fetching attempt #3 failed')
                    print(f'{term}: no xml returned after three tries')
                    return None

    if not parsed_data['searchresults']:
        logging.info(f'No data returned for {term}')
        return None

    # We sort the courses here, before we save it to disk, so that we don't
    # need to re-sort every time we load from disk.
    parsed_data['searchresults']['course'].sort(key=lambda c: c['clbid'])

    # Embed the term into each course individually
    for course in parsed_data['searchresults']['course']:
        course['term'] = term

    if not dry_run:
        destination = make_xml_term_path(term)
        serialized_data = xmltodict.unparse(parsed_data, pretty=True)
        save_data(serialized_data, destination)
        logging.debug(f'Fetched {destination}')

    return parsed_data


def load_term(term, force_download=False, dry_run=False):
    if not force_download:
        try:
            logging.info(f'Loading {term} from disk')
            term_path = make_xml_term_path(term)
            with open(term_path, 'rb') as infile:
                data = xmltodict.parse(infile, force_list=['course'])
        except FileNotFoundError:
            logging.info(f'Requesting {term} from server')
            data = load_data_from_server(term, dry_run=dry_run)
    else:
        logging.info(f'Forced to request {term} from server')
        data = load_data_from_server(term, dry_run=dry_run)

    if data:
        for course in data['searchresults']['course']:
            yield course
