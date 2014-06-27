#!/usr/local/bin/python3

from collections import OrderedDict
from argparse import ArgumentParser
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
import functools
from datetime import datetime
from bs4 import BeautifulSoup
import xmltodict
import requests
import sqlite3
import json
import time
import csv
import os
import re

data_path   = './'


class Term:
	def __init__(self, term, force=False, dry_run=False, output_type='json'):
		self.term = term
		self.dry_run = dry_run
		self.force_download = force
		self.output_type = output_type
		self.courses = {}

		print('Starting', self.term)
		create_database()

		# Get the XML data, and immediately write it out.
		self.load()
		if not self.raw_term_data:
			return

		self.process()

	def request_term_from_server(self):
		url = 'http://www.stolaf.edu/sis/public-acl-inez.cfm?searchyearterm=' \
			+  str(self.term) \
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

	def fix_invalid_xml(self):
		# Replace any invalid XML entities with &amp;
		regex = re.compile(r'&(?!(?:[a-z]+|#[0-9]+|#x[0-9a-f]+);)')
		subst = "&amp;"
		cleaned = re.sub(regex, subst, raw)
		return cleaned

	def load_data_from_server(self):
		raw_data = self.request_term_from_server(self.term)
		valid_data = self.fix_invalid_xml()
		save_data(valid_data, self.xml_term_path)
		print(self.xml_term_path)
		return valid_data

	def load(self):
		self.xml_term_path = data_path + 'raw_xml/' + str(self.term) + '.xml'

		if not self.force_download:
			try:
				print('Loading', self.term, 'from disk')
				raw_data = load_data_from_file(self.xml_term_path)
			except FileNotFoundError:
				print('Requesting', self.term, 'from server')
				raw_data = self.load_data_from_server()
		else:
			print('Forced to request', self.term, 'from server')
			raw_data = self.load_data_from_server()

		pydict = xmltodict.parse(raw_data)
		if pydict['searchresults']:
			self.raw_term_data = pydict['searchresults']['course']
		else:
			print('No data returned for', self.term)

	def process(self):
		# Process the raw data into a Python dictionary
		with ThreadPool(processes=4) as pool:
			mapped_course_processor = functools.partial(Course, 
				term=self.term, 
				output_type=self.output_type,
				dry_run=self.dry_run)
			mapped_courses = pool.map(mapped_course_processor, self.raw_term_data)

		for processed_course in mapped_courses:
			course = processed_course.details
			self.courses[course['clbid']] = course

			if not self.dry_run:
				with sqlite3.connect('courses.db') as connection:
					c = connection.cursor()
					# create a sql query with named placeholders automatically from the course dict
					no_list_course = {key: '/'.join(item) if type(item) is list else item for key, item in course.items()}
					columns = ', '.join(no_list_course.keys())
					placeholders = ':'+', :'.join(no_list_course.keys())
					query = 'INSERT OR REPLACE INTO courses (%s) VALUES (%s)' % (columns, placeholders)
					connection.execute(query, no_list_course)
					connection.commit()

		ordered_term_data = OrderedDict(sorted(self.courses.items()))

		if not self.dry_run:
			if self.output_type == 'csv':
				csv_term_data = sorted(courses.values(), key=lambda course: course['clbid'])
				save_data_as_csv(csv_term_data, data_path + 'terms/' + str(self.term) + '.csv')

			elif self.output_type == 'json':
				json_term_data = json.dumps(ordered_term_data, indent='\t', separators=(',', ': '))
				save_data(json_term_data, data_path + 'terms/' + str(self.term) + '.json')

			else:
				print('What kind of file is a "' + str(self.output_type) + '" file?')

		print('Done with', self.term)

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

class Course:
	def __init__(self, details, term, dry_run, output_type):
		self.output_type = output_type
		self.details = details
		self.dry_run = dry_run
		self.term = term

		self.details = {}
		self.padded_clbid = ''

		self.process()

	def request_detailed_course_data(self):
		url = 'https://www.stolaf.edu/sis/public-coursedesc.cfm?clbid=' + self.padded_clbid
		time.sleep(.5)
		request = requests.get(url)
		return request.text

	def get_details(self):
		html_term_path = data_path + 'details/' + str(self.padded_clbid) + '.html'

		try:
			# print('Loading', self.padded_clbid, 'from disk')
			raw_data = load_data_from_file(html_term_path)
		except FileNotFoundError:
			# print('Nope. Requesting', self.padded_clbid, 'from server')
			raw_data = self.request_detailed_course_data()
			save_data(raw_data, html_term_path)

		soup = BeautifulSoup(raw_data, 'lxml')
		strings = soup('p')

		apology = 'Sorry, no description'

		# TODO: Update this to be more infallible if the description runs to
		# multiple lines.

		if apology in strings[0].text or apology in strings[1].text:
			self.details['desc'] = strings[0].text
		else:
			self.details['title'] = strings[1].text
			if self.details.get('title'):
				# Remove extra spaces from the string
				self.details['title'] = ' '.join(self.details['title'].split())
				# Remove the course time info from the end
				self.details['title'] = self.details['title'].split('(')[0]
				# Remove anything before the first colon; reinsert the rest of the colons.
				self.details['title'] = ':'.join(self.details['title'].split(':')[1:]).strip()

			self.details['desc'] = ' '.join(strings[2].text.split()) if strings[2].text else ''

		if (self.details.get('desc') == '') or (apology in self.details['desc']):
			self.details['desc'] = None
		if self.details.get('title') == '':
			self.details['title'] = None

	def break_apart_departments(self):
		# Split apart the departments, because 'AR/AS' is actually
		# ['ART', 'ASIAN'] departments.
		split = self.details['deptname'].split('/')
		self.details['depts'] = [
			departments[dept] if dept in departments.keys() else dept for dept in split
		]

	def split_and_flip_instructors(self):
		# Take a string like 'Bridges IV, William H.' and split/flip it
		# to 'William H. Bridges IV'. Oh, and do that for each professor.
		if self.details['profs']:
			self.details['profs'] = parse_links_for_text(self.details['profs'])
			flippedProfs = []
			for prof in self.details['profs']:
				stringToSplit = prof.split(',')
				actualName = ''
				for namePart in reversed(stringToSplit):
					namePart = namePart.strip()
					actualName += namePart + ' '
				flippedProfs.append(actualName.strip())
			self.details['profs'] = flippedProfs

	def clean(self):
		# Unescape &amp; in course names
		self.details['name'] = self.details['coursename'].replace('&amp;', '&')
		del self.details['coursename']

		self.details['sect'] = self.details['coursesection']
		del self.details['coursesection']

		# Remove <br> tags from the 'notes' field.
		if self.details['notes']:
			self.details['notes'] = self.details['notes'].replace('<br>', ' ')
			self.details['notes'] = ' '.join(self.details['notes'].split())

		# Remove coursestatus and varcredits
		del self.details['coursestatus']
		del self.details['varcredits']

		# Flesh out coursesubtype
		if self.details['coursesubtype'] and self.details['coursesubtype'] in course_types:
			self.details['type'] = course_types[self.details['coursesubtype']]
		else:
			self.details['type'] = self.details['coursesubtype']
			print(self.details['type'], 'doesn\'t appear in the types list.')
		del self.details['coursesubtype']

		# Break apart dept names into lists
		self.break_apart_departments()
		del self.details['deptname']

		# Turn numbers into numbers
		self.details['clbid']   = int(self.details['clbid'])
		if 'X' not in self.details['coursenumber']:
			self.details['num'] = int(self.details['coursenumber'])
		else:
			self.details['num'] = self.details['coursenumber']
		del self.details['coursenumber']
		self.details['credits'] = float(self.details['credits'])
		self.details['crsid']   = int(self.details['crsid'])
		if self.details['groupid']: self.details['groupid'] = int(self.details['groupid'])

		# Turn booleans into booleans
		self.details['pf'] = True if self.details['pn'] is 'Y' else False
		del self.details['pn']

		# Add the term, year, and semester
		# term looks like 20083, where the first four are the year and the last one is the semester
		self.details['term'] = self.term
		self.details['year'] = int(str(self.term)[:4])  # Get the first four digits
		self.details['sem']  = int(str(self.term)[4])   # Get the last digit

		# Add the course level
		if type(self.details['num']) is int:
			self.details['level'] = int(self.details['num'] / 100) * 100
		elif 'X' in self.details['num']:
			self.details['level'] = int(self.details['num'][0]) * 100
		else:
			raise UserWarning('Course number is weird in', self.details)

		# Shorten meetinglocations, meetingtimes, and instructors
		self.details['places'] = self.details['meetinglocations']
		del self.details['meetinglocations']
		self.details['times']  = self.details['meetingtimes']
		del self.details['meetingtimes']
		self.details['profs']  = self.details['instructors']
		del self.details['instructors']

		# Pull the text contents out of various HTML elements as lists
		self.split_and_flip_instructors()
		if self.details['gereqs']: self.details['gereqs'] = parse_links_for_text(self.details['gereqs'])
		if self.details['places']: self.details['places'] = parse_links_for_text(self.details['places'])
		if self.details['times']:  self.details['times']  = get_contents_of_br_as_list(self.details['times'])

	def process(self):
		# save the full clbid
		self.padded_clbid = self.details['clbid']
		self.clean()

		# update merges two dicts
		self.get_details()

		if self.output_type == 'csv':
			self.details = OrderedDict(sorted(self.details.items()))
		else:
			if self.details.get('title') == self.details.get('name'):
				del self.details['name']
			if not self.details.get('title') and self.details.get('name'):
				self.details['title'] = self.details['name']
			cleanedcourse = {key: value for key, value in self.details.items() if value is not None}
			self.details = OrderedDict(sorted(cleanedcourse.items()))


########
# Utilities
######

def parse_links_for_text(stringWithLinks):
	soup = BeautifulSoup(stringWithLinks, 'lxml')
	return [link.get_text() for link in soup.find_all('a')]


def get_contents_of_br_as_list(stringWithBr):
	soup = BeautifulSoup(stringWithBr, 'lxml')
	return [item for item in soup.strings]


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
	with open(filepath, mode='w+', newline='\n') as outfile:
		outfile.write(data)

	print('Wrote', filename, 'term data; %d bytes.' % (len(data)))


def save_data_as_csv(data, filepath):
	ensure_dir_exists(filepath)
	filename = os.path.split(filepath)[1]
	with open(filepath, 'w+') as outfile:
		csv_file = csv.DictWriter(outfile, data[0].keys())
		csv_file.writeheader()
		csv_file.writerows(data)

	print('Wrote', filename, 'term data; %d bytes.' % (len(data)))


def create_database():
	with sqlite3.connect('courses.db') as connection:
		c = connection.cursor()
		c.execute('''CREATE TABLE IF NOT exists courses (
			id         INTEGER PRIMARY KEY,
			clbid      INTEGER UNIQUE,
			crsid      INTEGER,
			depts      TEXT,
			sect       TEXT,
			num        INTEGER,
			name       TEXT,
			title      TEXT,
			desc       TEXT,
			notes      TEXT,
			halfcredit INTEGER,
			varcredits BOOLEAN,
			status     TEXT,
			type       TEXT,
			credits    FLOAT,
			groupid    INTEGER,
			grouptype  TEXT,
			pf         BOOLEAN,
			term       TEXT,
			year       INTEGER,
			sem        INTEGER,
			level      INTEGER,
			places     TEXT,
			times      TEXT,
			profs      TEXT,
			gereqs     TEXT,
			prereqs    TEXT,
			coreqs     TEXT)
		''')


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
	with Pool(processes=4) as pool:
		mapped_term_processor = functools.partial(Term, 
			force=args.force, 
			output_type='csv' if args.csv_output else 'json', 
			dry_run=args.dry)
		pool.map(mapped_term_processor, terms)

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


if __name__ == '__main__':
	main()
