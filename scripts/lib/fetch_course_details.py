from argparse import ArgumentParser
from bs4 import BeautifulSoup
import functools
import requests
import re

from .load_data_from_file import load_data_from_file
from .paths import details_source, make_html_path
from .save_data import save_data
from .log import log, log_err


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
	details = {}

	if not force_download:
		try:
			# log('Loading', clbid, 'from disk')
			raw_data = load_data_from_file(html_term_path)
			soup = BeautifulSoup(raw_data)
		except FileNotFoundError:
			# log('Nope. Requesting', clbid, 'from server')
			raw_data = request_detailed_course_data(clbid)
			soup = clean_markup(raw_data, clbid, dry_run)
	else:
		# log('Forced to request', clbid, 'from server')
		raw_data = request_detailed_course_data(clbid)
		soup = clean_markup(raw_data, clbid, dry_run)

	return soup


def clean_markup(raw_data, clbid, dry_run):
	soup = BeautifulSoup(raw_data)

	# Clean up the HTML
	# .decompose() destroys the tag and all contents.
	# .unwrap() removes the tag and returns the contents.
	if soup.head:
		bookstoremsg = '\nTo find books for this class, please visit the\n'
		soup.head.decompose()
		soup.body.find(id='bigbodymainstyle').unwrap()
		soup.find(class_='sis-smallformfont').decompose()
		for tag in soup.find_all('script'): tag.decompose()
		for tag in soup.find_all(href='JavaScript:window.close();'):
			# It's a pointless link, wrapped in two <p>s.
			tag.parent.unwrap()
			tag.parent.unwrap()
			tag.decompose()
		for tag in soup.find_all(href='JavaScript:sis_openwindow(\'http://www.stolafbookstore.com/home.aspx\');'):
			tag.unwrap()
		empty_tags = soup.find_all(lambda tag: tag.name == 'p' and tag.find(True) is None and
			(tag.string is None or tag.string.strip()==""))
		for tag in empty_tags:
			tag.decompose()
		for string in soup.find_all(text=re.compile(bookstoremsg)):
			string.parent.decompose()
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
	apology = 'Sorry, no description is available for this course.'

	details = {}

	# Possibilities:
	# One paragraph, apology.
	# Two paragraphs, the second is the title, repeated.
	# Two or more paragraphs; everything after the first is the description.

	if strings[0] == apology:
		details['title'] = None
		details['desc'] = None
	else:
		details['title'] = strings[0].text
		if len(strings) >= 2:
			desc_strings = [' '.join(string.text.split()) for string in strings[1:]]
			details['desc'] = '\n'.join(desc_strings)

	if details.get('title'):
		# Remove extra spaces from the string
		details['title'] = ' '.join(details['title'].split())
		# Remove the course time info from the end
		details['title'] = details['title'].split('(')[0]
		# Remove anything before the first colon; reinsert the rest of the colons.
		details['title'] = ':'.join(details['title'].split(':')[1:])
		# Clean any extra whitespace off the title
		details['title'] = details['title'].strip()

	if details.get('desc'):
		# Remove silly endings and beginnings
		for ending in bad_endings:
			details['desc'] = ' '.join(details['desc'].split(ending))
		for beginning in bad_beginnings:
			details['desc'] = ' '.join(details['desc'].split(beginning))
		# Clean any extra whitespace off the description
		details['desc'] = details['desc'].strip()

	desc = details.get('desc')
	title = details.get('title')

	if desc == '':         details['desc'] = None
	elif desc == apology:  details['desc'] = None
	elif desc == title:    details['desc'] = None

	if title == '':
		details['title'] = None

	return details


def process_course_info(clbid, dry_run, force_download):
	clbid = str(clbid).zfill(10)

	soup = get_details(clbid, force_download, dry_run)
	details = clean_details(soup)

	return (clbid, details)


def fetch_course_details(clbids, dry_run=False, force_download=False):
	process_course_info_partial = functools.partial(process_course_info,
		force_download=force_download,
		dry_run=dry_run)

	mapped_details = map(process_course_info_partial, clbids)

	return dict(mapped_details)


def main():
	argparser = ArgumentParser()
	argparser.add_argument('clbids', type=int, nargs='*')
	argparser.add_argument('--workers', '-w', type=int, default=4)
	argparser.add_argument('--force-download', '-f', action='store_true')
	args = argparser.parse_args()

	details = fetch_course_details(**vars(args))


if __name__ == '__main__':
	main()
