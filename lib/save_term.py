import json

from .log import log
from .save_data import save_data
from .paths import make_built_term_path
from .csvify import csvify
from .xmlify import xmlify


def save_json_term(term_path, courses):
    json_term_data = json.dumps(courses,
                                indent='\t',
                                separators=(',', ': '),
                                sort_keys=True)
    save_data(json_term_data + '\n', term_path)


def save_csv_term(term_path, courses):
    csv_term_data = csvify(courses)
    save_data(csv_term_data + '\n', term_path)


def save_xml_term(term_path, courses):
    xml_term_data = xmlify(courses)
    save_data(xml_term_data + '\n', term_path)


def save_term(term, courses, kind):
    if not courses:
        return

    term_path = make_built_term_path(term, kind)
    log('saving term', term, 'to', term_path)
    if kind == 'json':
        save_json_term(term_path, courses)
    elif kind == 'csv':
        save_csv_term(term_path, courses)
    elif kind == 'xml':
        save_xml_term(term_path, courses)
