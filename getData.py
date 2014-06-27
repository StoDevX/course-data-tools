#!/usr/local/bin/python3

from collections import OrderedDict
from argparse import ArgumentParser
from datetime import datetime
from bs4 import BeautifulSoup
import xmltodict
import requests
import json
import time
import csv
import os
import re

data_path   = './'


########
# Utilities
######

def ensure_dir_exists(folder):
	'''Make sure that a folder exists.'''
	d = os.path.dirname(folder)
	if not os.path.exists(d):
		os.makedirs(d)


def load_data_from_file(filename):
	with open(filename, 'r') as infile:
		content = infile.read()
		return content


def save_data(data, filepath):
	ensure_dir_exists(filepath)
	filename = os.path.split(filepath)[1]
	with open(filepath, 'w+') as outfile:
		outfile.write(data)

	print('Wrote', filename, 'term data; %d bytes.' % (len(data)))


def load_data_from_server(term, xml_term_path):
	raw_data = request_term_from_server(term)
	valid_data = fix_invalid_xml(raw_data)
	save_data(valid_data, xml_term_path)
	print(xml_term_path)
	return valid_data


def save_data_as_csv(data, filepath):
	ensure_dir_exists(filepath)
	filename = os.path.split(filepath)[1]
	with open(filepath, 'w+') as outfile:
		csv_file = csv.DictWriter(outfile, data[0].keys())
		csv_file.writeheader()
		csv_file.writerows(data)

	print('Wrote', filename, 'term data; %d bytes.' % (len(data)))


########
# Calculations
######

def year_plus_term(year, term):
	return int(str(year) + str(term))


def find_terms(start_year=None, end_year=None):
	start_year    = start_year if start_year else 1994
	current_year  = end_year if end_year else datetime.now().year
	current_month = datetime.now().month
	term_list     = []

	most_years    = [year for year in range(start_year, current_year)]
	all_terms     = [1, 2, 3, 4, 5]
	limited_terms = [1, 2, 3]

	# Create a list of numbers like 20081 by concatenating the year and term
	# from 2008 to the year before this one.
	term_list = [year_plus_term(year, term) for year in most_years for term in all_terms]

	# Sort the list of terms to 20081, 20082, 20091 (instead of 20081, 20091, 20082)
	# (sorts in-place)
	term_list.sort()

	# St. Olaf publishes initial Fall, Interim, and Spring data in April of each year.
	# Full data is published by August.
	if start_year is not current_year:
		if current_month <= 3:
			current_year += 0
		elif current_month >= 4 and current_month <= 7:
			term_list += [year_plus_term(current_year, term) for term in limited_terms]
		elif current_month >= 8:
			term_list += [year_plus_term(current_year, term) for term in all_terms]
	else:
		term_list += [year_plus_term(current_year, term) for term in all_terms]

	return term_list


########
# Requests
######

def request_term_from_server(term):
	url = 'http://www.stolaf.edu/sis/public-acl-inez.cfm?searchyearterm=' \
		+  str(term) \
		+ '&searchkeywords=&searchdepts=&searchgereqs=&searchopenonly=off&' \
		+ 'searchlabonly=off&searchfsnum=&searchtimeblock=' \

	request = requests.get(url)

	if 'Sorry, there\'s been an error.' in request.text:
		print('Error in', url)
		print('Whoops! Made another error in the server.')
		if 'The request has exceeded the allowable time limit' in request.text:
			print('And that error is exceeding the time limit. Again.')
			print('We should probably do something about that.')

		return

	return request.text


def request_detailed_course_data(clbid):
	url = 'https://www.stolaf.edu/sis/public-coursedesc.cfm?clbid=' + clbid
	time.sleep(.5)
	request = requests.get(url)
	return request.text


########
# Loading
######

def fix_invalid_xml(raw):
	# print(raw)
	regex = re.compile(r'&(?!(?:[a-z]+|#[0-9]+|#x[0-9a-f]+);)')
	test_str = "&apos;M2&SC280&apos;);\"&gt;M 2 & SC280&lt;"
	subst = "&amp;"
	cleaned = re.sub(regex, subst, raw)
	return cleaned


def get_term(term, force=False):
	xml_term_path = data_path + 'raw_xml/' + str(term) + '.xml'

	if not force:
		try:
			print('Loading', term, 'from disk')
			raw_data = load_data_from_file(xml_term_path)
		except FileNotFoundError:
			print('Requesting', term, 'from server')
			raw_data = load_data_from_server(term, xml_term_path)
	else:
		print('Forced to request', term, 'from server')
		raw_data = load_data_from_server(term, xml_term_path)

	pydict = xmltodict.parse(raw_data)
	if pydict['searchresults']:
		return pydict['searchresults']['course']
	else:
		print('No data returned for', term)


def get_detailed_course_data(clbid):
	html_term_path = data_path + 'details/' + str(clbid) + '.html'

	try:
		# print('Loading', clbid, 'from disk')
		raw_data = load_data_from_file(html_term_path)
	except FileNotFoundError:
		# print('Nope. Requesting', clbid, 'from server')
		raw_data = request_detailed_course_data(clbid)
		save_data(raw_data, html_term_path)

	soup = BeautifulSoup(raw_data, 'lxml')
	strings = soup('p')

	course = {
		'title': None,
		'desc': None
	}

	apology = 'Sorry, no description'

	# TODO: Update this to be more infallible if the description runs to
	# multiple lines.

	if apology in strings[0].text or apology in strings[1].text:
		course['desc'] = strings[0].text
	else:
		course['title'] = strings[1].text
		if course['title']:
			# Remove extra spaces from the string
			course['title'] = ' '.join(course['title'].split())
			# Remove the course time info from the end
			course['title'] = course['title'].split('(')[0]
			# Remove anything before the first colon; reinsert the rest of the colons.
			course['title'] = ':'.join(course['title'].split(':')[1:]).strip()

		course['desc'] = ' '.join(strings[2].text.split()) if strings[2].text else ''

	if course['desc'] == '' or apology in course['desc']:
		course['desc'] = None
	if course['title'] == '':
		course['title'] = None

	return course


########
# Parsing Tools
######

departments = {
	'AR': 'ART',
	'AS': 'ASIAN',
	'BI': 'BIO',
	'CH': 'CHEM',
	'EC': 'ECON',
	'ES': 'ENVST',
	'HI': 'HIST',
	'MU': 'MUSIC',
	'PH': 'PHIL',
	'PS': 'PSCI',
	'RE': 'REL',
	'SA': 'SOAN'
}

course_types = {
	'L': 'Lab',
	'D': 'Discussion',
	'S': 'Seminar',
	'T': 'Topic',
	'F': 'FLAC',
	'R': 'Research'
}


def parseLinksForText(stringWithLinks):
	soup = BeautifulSoup(stringWithLinks, 'lxml')
	return [link.get_text() for link in soup.find_all('a')]


def getContentsOfBrAsList(stringWithBr):
	soup = BeautifulSoup(stringWithBr, 'lxml')
	return [item for item in soup.strings]


def breakApartDepartments(stringToBreak):
	# Split apart the departments, because 'AR/AS' is actually
	# ['ART', 'ASIAN'] departments.
	broken = stringToBreak.split('/')
	return [departments[dept] if dept in departments.keys() else dept for dept in broken]


def splitAndFlipInstructors(instructors):
	# Take a string like 'Bridges IV, William H.' and split/flip it
	# to 'William H. Bridges IV'. Oh, and do that for each professor.
	flippedProfs = []
	for prof in instructors:
		stringToSplit = prof.split(',')
		actualName = ''
		for namePart in reversed(stringToSplit):
			namePart = namePart.strip()
			actualName += namePart + ' '
		flippedProfs.append(actualName.strip())
	return flippedProfs


########
# Processing
######

def clean_course(course, term):
	# Unescape &amp; in course names
	course['name'] = course['coursename'].replace('&amp;', '&')
	del course['coursename']

	course['sect'] = course['coursesection']
	del course['coursesection']

	# Remove <br> tags from the 'notes' field.
	if course['notes']:
		course['notes'] = course['notes'].replace('<br>', ' ')
		course['notes'] = ' '.join(course['notes'].split())

	# Remove coursestatus and varcredits
	del course['coursestatus']
	del course['varcredits']

	# Flesh out coursesubtype
	if course['coursesubtype'] and course['coursesubtype'] in course_types:
		course['type'] = course_types[course['coursesubtype']]
	else:
		course['type'] = course['coursesubtype']
		print(course['type'], 'doesn\'t appear in the types list.')
	del course['coursesubtype']

	# Break apart dept names into lists
	course['depts'] = breakApartDepartments(course['deptname'])
	del course['deptname']

	# Turn numbers into numbers
	course['clbid']   = int(course['clbid'])
	if 'X' not in course['coursenumber']:
		course['num'] = int(course['coursenumber'])
	else:
		course['num'] = course['coursenumber']
	del course['coursenumber']
	course['credits'] = float(course['credits'])
	course['crsid']   = int(course['crsid'])
	if course['groupid']: course['groupid'] = int(course['groupid'])

	# Turn booleans into booleans
	course['pf'] = True if course['pn'] is 'Y' else False
	del course['pn']

	# Add the term, year, and semester
	# term looks like 20083, where the first four are the year and the last one is the semester
	course['term'] = term
	course['year'] = int(str(term)[:4])  # Get the first four digits
	course['sem']  = int(str(term)[4])   # Get the last digit

	# Add the course level
	if type(course['num']) is int:
		course['level'] = int(course['num'] / 100) * 100
	elif 'X' in course['num']:
		course['level'] = int(course['num'][0]) * 100
	else:
		raise UserWarning('Course number is weird in', course)

	# Shorten meetinglocations, meetingtimes, and instructors
	course['places'] = course['meetinglocations']
	del course['meetinglocations']
	course['times']  = course['meetingtimes']
	del course['meetingtimes']
	course['profs']  = course['instructors']
	del course['instructors']

	# Pull the text contents out of various HTML elements as lists
	if course['profs']:  course['profs']  = splitAndFlipInstructors(parseLinksForText(course['profs']))
	if course['gereqs']: course['gereqs'] = parseLinksForText(course['gereqs'])
	if course['places']: course['places'] = parseLinksForText(course['places'])
	if course['times']:  course['times']  = getContentsOfBrAsList(course['times'])

	return course


def process_course(course, term, csv_output=False):
	# save the full clbid
	padded_clbid = course['clbid']
	course = clean_course(course, term)

	# update merges two dicts
	detailed_course = get_detailed_course_data(padded_clbid)
	course.update(detailed_course)

	if csv_output:
		return OrderedDict(sorted(course.items()))
	else:
		if course['title'] == course['name']:
			del course['name']
		if not course['title'] and course['name']:
			course['title'] = course['name']
		cleanedcourse = {}
		cleanedcourse.update((key, value) for key, value in course.items() if value is not None)
		return OrderedDict(sorted(cleanedcourse.items()))


########
# Main
######

def term_processor(term, data=[], force=False, csv_output=False, dry_run=False):
	print('Starting', term)

	# Get the XML data, and immediately write it out.
	raw_term_data = get_term(term, force=force)
	if not raw_term_data:
		return
	term_data = {}

	# Process the raw data into a Python dictionary
	for course in raw_term_data:
		processed_course = process_course(course, term, csv_output)
		clbid = processed_course['clbid']
		term_data[clbid] = processed_course
		data.append(processed_course)

	ordered_term_data = OrderedDict(sorted(term_data.items()))

	if dry_run:
		print('Done with', term)
		return

	if csv_output:
		csv_term_data = sorted(term_data.values(), key=lambda course: course['clbid'])
		save_data_as_csv(csv_term_data, data_path + 'terms/' + str(term) + '.csv')

	else:  # then JSON output
		json_term_data = json.dumps(ordered_term_data, indent='\t', separators=(',', ': '))
		save_data(json_term_data, data_path + 'terms/' + str(term) + '.json')

	print('Done with', term)


def main():
	global output_type

	argparser = ArgumentParser(description='Fetch term data from the SIS.')

	argparser.add_argument('--terms',
		type=int,
		nargs='*',
		help='Terms for which request data from the SIS')

	argparser.add_argument('--years',
		type=int,
		nargs='*',
		help='Entire years for which request data from the SIS')

	argparser.add_argument('--force', '-f',
		action='store_true',
		help='Force reloading of the specified course')

	argparser.add_argument('--dry', '-d',
		action='store_true',
		help='Only print output; don\'t write files.')

	argparser.add_argument('--csv-output',
		action='store_true',
		help='If set, the output will be in CSV files')

	args = argparser.parse_args()

	# If terms are provided at the terminal, process only those terms.
	# Otherwise, `args.terms` is None, so find_terms will run.
	terms = args.terms or ([] if args.years else find_terms())

	if args.years:
		for year in args.years:
			terms += find_terms(year, year)

	all_terms = []
	for term in terms:
		term_processor(term,
			data=all_terms,
			force=args.force,
			csv_output=args.csv_output,
			dry_run=args.dry)

	sorted_terms = {}
	filtered_data = set()
	for course in all_terms:
		terms = ['Concurrent', 'Prerequisite', 'conjunction', 'Offered', 'Required', 'Open to']
		deptstr = '/'.join(course['depts'])
		prereqs = course.get('desc', '')
		times = ' | '.join(course.get('times', ''))
		sorted_terms[course['crsid']] = \
			str(deptstr) + ' ' + str(course['num'])
		filtered_data.add(times)

	# print(sorted(filtered_data))

	# print(
	# 	json.dumps(
	# 		OrderedDict(sorted(sorted_terms.items())),
	# 		indent='  ',
	# 		separators=(',', ': ')
	# 	)
	# )


if __name__ == '__main__':
	main()
