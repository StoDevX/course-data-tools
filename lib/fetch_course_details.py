import requests
import logging
import json
import html
import re

from .paths import make_detail_path
from .save_data import save_data

apology = 'Sorry, no description is available for this course.'

bad_endings = [
    'Click on course title in the Class & Lab for more information about the course for that term.',
    'For more information on this course please see the following website: http://www.stolaf.edu/depts/english/courses/',
]

bad_beginnings = []

html_regex = re.compile(r'<[^>]*>')


def request_detailed_course_data(clbid):
    url = f'https://www.stolaf.edu/sis/public-coursedesc-json.cfm?clbid={clbid}'
    r = requests.get(url)
    r.raise_for_status()
    return r.text


def get_details(clbid, force_download, dry_run):
    html_term_path = make_detail_path(clbid)

    if not force_download:
        try:
            logging.debug(f'Loading {clbid} from disk')
            with open(html_term_path, 'r', encoding='utf-8') as infile:
                soup = json.load(infile)
        except FileNotFoundError:
            logging.debug(f'Nope. Requesting {clbid} from server')
            raw_data = request_detailed_course_data(clbid)
            soup = clean_markup(raw_data, clbid, dry_run)
    else:
        logging.debug(f'Forced to request {clbid} from server')
        raw_data = request_detailed_course_data(clbid)
        soup = clean_markup(raw_data, clbid, dry_run)

    return soup


def clean_markup(raw_data, clbid, dry_run):
    start_str = '<!-- content:start -->'
    end_str = '<!-- content:end -->'

    try:
        start_idx = raw_data.index(start_str) + len(start_str)
        end_idx = raw_data.index(end_str)
    except ValueError:
        raise Exception(f'"{clbid}" did not return any data, or returned an error')

    extracted_data = raw_data[start_idx:end_idx]
    data = json.loads(extracted_data)

    if len(data) == 0:
        raise Exception(f'"{clbid}" had zero results! {extracted_data}')
    elif len(data) > 1:
        raise Exception(f'"{clbid}" had more than one result! {extracted_data}')

    data = data[clbid]

    if not dry_run:
        detail_path = make_detail_path(clbid)
        save_data(json.dumps(data, indent='\t', ensure_ascii=False, sort_keys=True) + '\n', detail_path)

    return data


def sanitize_for_unicode(string: str):
    # Remove html entities
    string = html.unescape(string)

    string = string.replace('\u0091', '‘')
    string = string.replace('\u0092', '’')
    string = string.replace('\u0093', '“')
    string = string.replace('\u0094', '”')

    string = string.replace('\u0096', '–')
    string = string.replace('\u0097', '—')

    string = string.replace('\u00ad', '-')
    string = string.replace('\u00ae', '®')

    return string


def clean_details(data):
    title = data['fullname'] if 'fullname' in data else None
    description = data['description'] if 'description' in data else None

    if title:
        title = sanitize_for_unicode(title)
        # Remove extra spaces from the string
        title = ' '.join(title.split())
        # Remove the course time info from the end
        title = title.split('(', maxsplit=1)[0]
        # FIXME: use this
        # title = re.sub(r'(.*)\(.*\)$', r'\1', title)
        # Clean any extra whitespace off the title
        title = title.strip()
        # Remove html tags from the title
        title = html_regex.sub('', title)

    if description:
        # Collect the paragraphs into a list of strings
        full_description = {}
        paragraph_index = 0
        for part in description:
            if not part:
                paragraph_index += 1
                continue
            full_description[paragraph_index] = f'{full_description.get(paragraph_index, "")} {part}'

        # Remove any remaining HTML tags
        description = [html_regex.sub('', para) for para in full_description.values()]

        # Remove extra spaces
        description = [' '.join(para.split()) for para in description]

        # Unescape any html entities
        # description = [html.unescape(para) for para in description]

        # Remove silly endings and beginnings
        for ending in bad_endings:
            description = [' '.join(para.split(ending))
                           if ending in para
                           else para
                           for para in description]
        for beginning in bad_beginnings:
            description = [' '.join(para.split(beginning))
                           if beginning in para
                           else para
                           for para in description]

        # Clean any extra whitespace off the description
        description = [para.strip() for para in description]

        # Remove any blank strings
        description = [sanitize_for_unicode(para) for para in description if para]

    if not description or description == [apology] or description == [title]:
        description = None

    if not title:
        title = None

    return {'title': title, 'description': description}


def fetch_course_details(clbid, dry_run=False, force_download=False):
    clbid = str(clbid).zfill(10)

    data = get_details(clbid, force_download, dry_run)
    return clean_details(data)
