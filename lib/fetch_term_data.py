import xmltodict
import requests
import re

from .load_data_from_file import load_data_from_file
from .paths import make_xml_term_path
from .save_data import save_data
from .log import log, log_err


def fix_invalid_xml(raw):
    # Replace any invalid XML entities with &amp;
    subst = '&amp;'
    cleaned = re.sub(r'&(?!(?:[a-z]+|#[0-9]+|#x[0-9a-f]+);)', subst, raw)
    return cleaned


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
            log_err('''And that error is exceeding the time limit. Again.
                We should probably do something about that.''')

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
        log('No data returned for', term)
        return None

    valid_data = fix_invalid_xml(raw_data)
    parsed_data = xmltodict.parse(valid_data, force_list=('course',))

    if not parsed_data['searchresults']:
        log('No data returned for', term)
        return None

    # We sort the courses here, before we save it to disk, so that we don't
    # need to re-sort every time we load from disk.
    parsed_data['searchresults']['course'].sort(key=lambda c: c['clbid'])

    embedded_terms = embed_term_in_courses(parsed_data, term)

    if not dry_run:
        reparsed_data = xmltodict.unparse(embedded_terms, pretty=True)
        save_data(reparsed_data, xml_term_path)
        # log('Fetched', xml_term_path)

    return embedded_terms


def unorder_dicts_in_term(term):
    term = dict(term.items())
    term['searchresults'] = dict(term['searchresults'].items())
    term['searchresults']['course'] = [dict(course.items())
                                       for course in term['searchresults']['course']]

    return term


def load_term(term, force_download=False, dry_run=False):
    xml_term_path = make_xml_term_path(term)

    if not force_download:
        try:
            # log('Loading', term, 'from disk')
            raw_data = load_data_from_file(xml_term_path)
            data = xmltodict.parse(raw_data, force_list=('course',))
        except FileNotFoundError:
            log('Requesting', term, 'from server')
            data = load_data_from_server(term, dry_run=dry_run)
    else:
        log('Forced to request', term, 'from server')
        data = load_data_from_server(term, dry_run=dry_run)

    data = unorder_dicts_in_term(data)
    return data
