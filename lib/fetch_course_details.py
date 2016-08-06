from bs4 import BeautifulSoup, SoupStrainer
import requests
import re

import logging
from .load_data_from_file import load_data_from_file
from .paths import make_html_path
from .save_data import save_data

apology = 'Sorry, no description is available for this course.'

bad_endings = [
    'Click on course title in the Class & Lab for more information about the course for that term.',
    'For more information on this course please see the following website: http://www.stolaf.edu/depts/english/courses/',
]

bad_beginnings = []


def request_detailed_course_data(clbid):
    url = 'https://www.stolaf.edu/sis/public-coursedesc.cfm?clbid=' + clbid
    request = requests.get(url)
    return request.text


def get_details(clbid, force_download, dry_run):
    html_term_path = make_html_path(clbid)

    if not force_download:
        try:
            logging.debug('Loading %d from disk', clbid)
            strainer = SoupStrainer('p')
            with open(html_term_path, 'r', encoding='utf-8') as infile:
                soup = BeautifulSoup(infile, 'html.parser', parse_only=strainer)
        except FileNotFoundError:
            logging.debug('Nope. Requesting %d from server', clbid)
            raw_data = request_detailed_course_data(clbid)
            soup = clean_markup(raw_data, clbid, dry_run)
    else:
        logging.debug('Forced to request %d from server', clbid)
        raw_data = request_detailed_course_data(clbid)
        soup = clean_markup(raw_data, clbid, dry_run)

    return soup


def is_empty_paragraph(tag):
    return (tag.name == 'p' and tag.find(True) is None and
            (tag.string is None or tag.string.strip() == ""))


def clean_markup(raw_data, clbid, dry_run):
    soup = BeautifulSoup(raw_data, 'html.parser')

    # Clean up the HTML
    # .decompose() destroys the tag and all contents.
    # .unwrap() removes the tag and returns the contents.
    if soup.head:
        bookstoremsg = '\nTo find books for this class, please visit the\n'
        soup.head.decompose()
        soup.body.find(id='bigbodymainstyle').unwrap()
        soup.find(class_='sis-smallformfont').decompose()
        for tag in soup.find_all('script'):
            tag.decompose()
        for tag in soup.find_all(href='JavaScript:window.close();'):
            # It's a pointless link, wrapped in two <p>s.
            tag.parent.unwrap()
            tag.parent.unwrap()
            tag.decompose()
        for tag in soup.find_all(href="JavaScript:sis_openwindow('http://www.stolafbookstore.com/home.aspx');"):
            tag.unwrap()

        empty_tags = soup.find_all(is_empty_paragraph)

        [tag.decompose() for tag in empty_tags]
        [string.parent.decompose()
         for string in soup.find_all(text=re.compile(bookstoremsg))]

        if soup.body.p.p:
            soup.body.p.unwrap()

        if soup.find(id='fusiondebugging'):
            soup.find(id='fusiondebugging').decompose()

    for tag in soup.select('p'):
        del tag['style']

    str_soup = str(soup)
    str_soup = re.sub(r' +', ' ', str_soup)
    str_soup = re.sub(r'\n+', '\n', str_soup)
    str_soup = str_soup.strip() + '\n'

    if not dry_run and (str_soup != raw_data):
        html_term_path = make_html_path(clbid)
        save_data(str_soup, html_term_path)

    return soup


def clean_details(soup):
    strings = soup('p')

    title = None
    description = None

    # Possibilities:
    # One paragraph, apology.
    # Two paragraphs, the second is the title, repeated.
    # Two or more paragraphs; everything after the first is the description.

    str0 = strings[0].text
    if str0 == apology:
        title = None
        description = None
    else:
        title = str0
        if len(strings) >= 2:
            desc_strings = [' '.join(string.text.split())
                            for string in strings[1:]]
            description = '\n'.join(desc_strings)

    if title:
        # Remove extra spaces from the string
        title = ' '.join(title.split())
        # Remove the course time info from the end
        title = title.split('(', maxsplit=1)[0]
        # Remove anything before the first colon; reinsert the rest of the colons.
        title = ':'.join(title.split(':')[1:])
        # Clean any extra whitespace off the title
        title = title.strip()

    if description:
        # Remove silly endings and beginnings
        for ending in bad_endings:
            if ending in description:
                description = ' '.join(description.split(ending))
        for beginning in bad_beginnings:
            if beginning in description:
                description = ' '.join(description.split(beginning))
        # Clean any extra whitespace off the description
        description = description.strip()

    if description == '' or description == apology or description == title:
        description = None

    if title == '':
        title = None

    return {'title': title, 'description': description}


def fetch_course_details(clbid, dry_run=False, force_download=False):
    clbid = str(clbid).zfill(10)

    soup = get_details(clbid, force_download, dry_run)
    return clean_details(soup)
