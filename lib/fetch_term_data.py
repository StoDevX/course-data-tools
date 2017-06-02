import xmltodict
import requests
import logging
import html

from .paths import make_xml_term_path
from .save_data import save_data


def request_term_from_server(term):
    url = f'http://www.stolaf.edu/sis/static-classlab/{term}.xml'

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


def load_data_from_server(term, dry_run=False):
    raw_data = request_term_from_server(term)
    if not raw_data:
        logging.info(f'No data returned for {term}')
        return None

    # Replace any invalid XML entities with their utf-8 equivalents
    valid_data = html.unescape(raw_data)

    # Parse the data into an actual data structure
    parsed_data = xmltodict.parse(valid_data, force_list=['course'])

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
