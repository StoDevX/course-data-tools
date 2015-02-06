#!/usr/bin/env python3

from concurrent.futures import ProcessPoolExecutor
from collections import OrderedDict
from argparse import ArgumentParser
from datetime import datetime
from bs4 import BeautifulSoup
import xmltodict
import functools
import itertools
import requests
import hashlib
import time
import json
import csv
import os
import re

details_source = './source/details/'
xml_source     = './source/raw_xml/'
term_dest      = './courses/terms/'
course_dest    = './source/courses/'
info_path      = './courses/info.json'
mappings_path  = './related-data/generated/'
handmade_path  = './related-data/handmade/'

quiet = False
dry_run = False

departments = None
with open(handmade_path + 'to_department_abbreviations.json') as depts:
	departments = json.loads(depts.read())

course_types = None
with open(handmade_path + 'course_types.json') as types:
	course_types = json.loads(types.read())


class Term:
	def __init__(self, term, args=None):
		self.term = term
		self.year = int(str(self.term)[:4])    # Get the first four digits
		self.semester = int(str(self.term)[4]) # Get the last digit

		self.force_download = args.force
		self.output_type = args.output_type
		self.single_thread = args.single_thread
		self.courses = []

		self.xml_term_path = xml_source + str(self.term) + '.xml'
		self.raw_term_data = None

		# Get the XML data, and immediately write it out.
		self.load()
		if not self.raw_term_data:
			return

		self.process()
		self.save()

	def request_term_from_server(self):
		# Yes, the request needs all of these extra parameters in order to run.
		url = 'http://www.stolaf.edu/sis/public-acl-inez.cfm?searchyearterm=' \
			+ str(self.term) \
			+ '&searchkeywords=&searchdepts=&searchgereqs=&searchopenonly=off&' \
			+ 'searchlabonly=off&searchfsnum=&searchtimeblock='

		request = requests.get(url)

		if 'Sorry, there\'s been an error.' in request.text:
			print('Error in', url)
			print('Whoops! Made another error in the server.')
			if 'The request has exceeded the allowable time limit' in request.text:
				print('And that error is exceeding the time limit. Again.')
				print('We should probably do something about that.')

			return

		return request.text

	def fix_invalid_xml(self, raw):
		# Replace any invalid XML entities with &amp;
		regex = re.compile(r'&(?!(?:[a-z]+|#[0-9]+|#x[0-9a-f]+);)')
		subst = '&amp;'
		cleaned = re.sub(regex, subst, raw)
		return cleaned

	def load_data_from_server(self):
		raw_data = self.request_term_from_server()
		valid_data = self.fix_invalid_xml(raw_data)
		xmldict = xmltodict.parse(valid_data)

		# TODO: Merge this bit with the similar bit below, in load.
		# I don't know where, but they serve the same purpose, just at different spots.

		reparsed_data = ''
		if xmldict['searchresults']:
			if type(xmldict['searchresults']['course']) is not list:
				xmldict['searchresults']['course'] = [xmldict['searchresults']['course']]
			xmldict['searchresults']['course'] = sorted(xmldict['searchresults']['course'], key=lambda c: c['clbid'])
			reparsed_data = xmltodict.unparse(xmldict, pretty=True)

		save_data(reparsed_data, self.xml_term_path)
		if not quiet: print('Fetched', self.xml_term_path)

		return valid_data

	def load(self):
		raw_data = ''
		if not self.force_download:
			try:
				if not quiet: print('Loading', self.term, 'from disk')
				raw_data = load_data_from_file(self.xml_term_path)
			except FileNotFoundError:
				if not quiet: print('Requesting', self.term, 'from server')
				raw_data = self.load_data_from_server()
		else:
			if not quiet: print('Forced to request', self.term, 'from server')
			raw_data = self.load_data_from_server()

		pydict = xmltodict.parse(raw_data)
		if pydict['searchresults']:
			# If there is only one course for a semester, then raw_term_data
			# is just an object; otherwise, it's a list. We need to ensure that
			# it is always a list.
			self.raw_term_data = pydict['searchresults']['course']
			if type(self.raw_term_data) is not list:
				self.raw_term_data = [self.raw_term_data]
		else:
			if not quiet: print('No data returned for', self.term)
			delete_file(self.xml_term_path)

	def process(self):
		if not quiet: print('Editing', self.term)

		# Process the raw data into a Python dictionary
		mapped_course_processor = functools.partial(Course, term=self.term, output_type=self.output_type)
		if not self.single_thread:
			with ProcessPoolExecutor(max_workers=8) as pool:
				mapped_courses = pool.map(mapped_course_processor, self.raw_term_data)
		else:
			mapped_courses = map(mapped_course_processor, self.raw_term_data)

		for processed_course in mapped_courses:
			course = processed_course.details
			self.courses.append(course)

		ordered_term_data = sorted(self.courses, key=lambda c: c['clbid'])

		self.ordered_term_data = ordered_term_data

	def save(self):
		if not dry_run:
			if self.output_type == 'json' or not self.output_type:
				json_term_data = json.dumps({'courses': self.ordered_term_data}, indent='\t', separators=(',', ': ')) + '\n'
				save_data(json_term_data, term_dest + str(self.term) + '.json')

			elif self.output_type == 'csv':
				csv_term_data = sorted(self.ordered_term_data, key=lambda c: c['clbid']) + '\n'
				save_data_as_csv(csv_term_data, term_dest + str(self.term) + '.csv')

			else:
				print('What kind of file is a "' + str(self.output_type) + '" file? (for ' + str(self.term) + ')')

		if not quiet: print('Done with', self.term)


KEYNOTFOUNDIN1 = '<KEY NOT FOUND IN 1>'       # KeyNotFound for dictDiff
KEYNOTFOUNDIN2 = '<KEY NOT FOUND IN 2>'       # KeyNotFound for dictDiff

def dict_diff(first, second):
	# from http://code.activestate.com/recipes/576644-diff-two-dictionaries/#c6
	"""
	Return a dict of keys that differ with another config object.  If a value is
	not found in one fo the configs, it will be represented by KEYNOTFOUND.
	@param first:   Fist dictionary to diff.
	@param second:  Second dicationary to diff.
	@return diff:   Dict of Key => (first.val, second.val)
	"""

	diff = {}
	sd1 = set(first)
	sd2 = set(second)
	# Keys missing in the second dict
	for key in sd1.difference(sd2):
		diff[key] = (first[key], KEYNOTFOUNDIN2)
	# Keys missing in the first dict
	for key in sd2.difference(sd1):
		diff[key] = (KEYNOTFOUNDIN1, second[key])
	# Check for differences
	for key in sd1.intersection(sd2):
		if first[key] != second[key]:
			diff[key] = (first[key], second[key])
	return diff

def get_old_dict_values(old, new):
	# Returns the "old" value for two dicts.
	diff = dict_diff(old, new)

	return {key: diff[key][0] for key in diff}


class Course:
	bad_endings = [
		'Click on course title in the Class & Lab for more information about the course for that term.',
		'For more information on this course please see the following website: http://www.stolaf.edu/depts/english/courses/',
	]

	bad_beginnings = []

	def __init__(self, details, term, output_type):
		self.output_type = output_type
		self.details = details
		self.revisions = []
		self.term = term
		self.padded_clbid = self.details['clbid'] # save the full clbid
		self.course_path = course_dest + find_details_subdir(self.padded_clbid) + '.json'

		self.clean()
		self.get_details()
		# self.extract_notes()
		# self.parse_prerequisites()
		self.process()

		self.check_for_revisions()
		self.save()

	def load_previous(self):
		try:
			prior_data = load_data_from_file(self.course_path)
			self.prior = json.loads(prior_data)
		except ValueError:
			self.prior = {}
		except FileNotFoundError:
			self.prior = {}

		if 'revisions' in self.prior:
			self.revisions = self.prior.get('revisions')
			del self.prior['revisions']

	def check_for_revisions(self):
		self.load_previous()

		diff = get_old_dict_values(self.prior, self.details)
		if diff:
			self.revisions.append(diff)
			print('Revision:', self.revisions)

		if self.revisions and ('revisions' not in self.details or self.revisions != self.details.get('revisions')):
			self.details['revisions'] = self.revisions

	def request_detailed_course_data(self):
		url = 'https://www.stolaf.edu/sis/public-coursedesc.cfm?clbid=' + self.padded_clbid
		request = requests.get(url)
		return request.text

	def get_details(self):
		html_term_path = details_source + find_details_subdir(self.padded_clbid) + '.html'

		try:
			# if not quiet: print('Loading', self.padded_clbid, 'from disk')
			raw_data = load_data_from_file(html_term_path)
		except FileNotFoundError:
			# if not quiet: print('Nope. Requesting', self.padded_clbid, 'from server')
			raw_data = self.request_detailed_course_data()
			save_data(raw_data, html_term_path)

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

		strings = soup('p')
		apology = 'Sorry, no description is available for this course.'

		# Possibilities:
		# One paragraph, apology.
		# Two paragraphs, the second is the title, repeated.
		# Two or more paragraphs; everything after the first is the description.

		if strings[0] == apology:
			self.details['title'] = None
			self.details['desc'] = None
		else:
			self.details['title'] = strings[0].text
			if len(strings) >= 2:
				desc_strings = [' '.join(string.text.split()) for string in strings[1:]]
				self.details['desc'] = '\n'.join(desc_strings)

		if self.details.get('title'):
			# Remove extra spaces from the string
			self.details['title'] = ' '.join(self.details['title'].split())
			# Remove the course time info from the end
			self.details['title'] = self.details['title'].split('(')[0]
			# Remove anything before the first colon; reinsert the rest of the colons.
			self.details['title'] = ':'.join(self.details['title'].split(':')[1:])
			# Clean any extra whitespace off the title
			self.details['title'] = self.details['title'].strip()

		if self.details.get('desc'):
			# Remove silly endings and beginnings
			for ending in Course.bad_endings:
				self.details['desc'] = ' '.join(self.details['desc'].split(ending))
			for beginning in Course.bad_beginnings:
				self.details['desc'] = ' '.join(self.details['desc'].split(beginning))
			# Clean any extra whitespace off the description
			self.details['desc'] = self.details['desc'].strip()

		if self.details.get('desc') == '':
			self.details['desc'] = None
		elif self.details.get('desc') == apology:
			self.details['desc'] = None
		elif self.details.get('desc') == self.details.get('title'):
			self.details['desc'] = None

		if self.details.get('title') == '':
			self.details['title'] = None

		str_soup = str(soup)
		str_soup = re.sub(r' +', ' ', str_soup)
		str_soup = re.sub(r'\n+', '\n', str_soup)
		str_soup = str_soup.strip() + '\n'

		save_data(str_soup, html_term_path)

	def break_apart_departments(self):
		# Split apart the departments, because 'AR/AS' is actually
		# ['ART', 'ASIAN'] departments.
		split = self.details['deptname'].split('/')
		self.details['depts'] = [
			departments[dept.lower()] if dept.lower() in departments.keys() else dept for dept in split
		]

	def split_and_flip_instructors(self):
		# Take a string like 'Bridges IV, William H.' and split/flip it
		# to 'William H. Bridges IV'. Oh, and do that for each professor.
		if self.details['instructors']:
			self.details['instructors'] = parse_links_for_text(self.details['instructors'])
			flipped_profs = []
			for prof in self.details['instructors']:
				string_to_split = prof.split(',')
				actual_name = ''
				for name_part in reversed(string_to_split):
					name_part = name_part.strip()
					actual_name += name_part + ' '
				flipped_profs.append(actual_name.strip())
			self.details['instructors'] = flipped_profs

	def clean(self):
		# Unescape &amp; in course names
		self.details['name'] = self.details['coursename'].replace('&amp;', '&')
		del self.details['coursename']

		self.details['section'] = self.details['coursesection']
		del self.details['coursesection']

		self.details['status'] = self.details['coursestatus']
		del self.details['coursestatus']

		# Remove <br> tags from the 'notes' field.
		if self.details['notes']:
			self.details['notes'] = self.details['notes'].replace('<br>', ' ')
			self.details['notes'] = ' '.join(self.details['notes'].split())

		# Remove the unused varcredits property
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
		if self.details['groupid']:
			self.details['groupid'] = int(self.details['groupid'])

		# Turn booleans into booleans
		self.details['pf'] = True if self.details['pn'] is 'Y' else False
		del self.details['pn']

		# Add the term, year, and semester
		# `term` looks like 20083, where the first four digits represent the
		# year, and the last digit represents the semester
		self.details['term']     = self.term
		self.details['year']     = int(str(self.term)[:4])  # Get the first four digits
		self.details['semester'] = int(str(self.term)[4])   # Get the last digit

		# Add the course level
		if type(self.details['num']) is int:
			self.details['level'] = int(self.details['num'] / 100) * 100
		elif 'X' in self.details['num']:
			self.details['level'] = int(self.details['num'][0]) * 100
		else:
			raise UserWarning('Course number is weird in', self.details)

		# Shorten meetinglocations, meetingtimes, and instructors
		self.details['locations'] = self.details['meetinglocations']
		del self.details['meetinglocations']
		self.details['times']  = self.details['meetingtimes']
		del self.details['meetingtimes']

		# Pull the text contents out of various HTML elements as lists
		self.split_and_flip_instructors()
		if self.details['gereqs']: self.details['gereqs'] = parse_links_for_text(self.details['gereqs'])
		if self.details['locations']: self.details['locations'] = parse_links_for_text(self.details['locations'])
		if self.details['times']:  self.details['times']  = parse_paragraph_as_list(self.details['times'])

	def parse_prerequisites(self):
		if self.details['desc'] and 'Prerequisite' in self.details['desc']:
			desc = self.details['desc']
			index = desc.index('Prerequisite')
			print(desc[index:])

	def extract_notes(self):
		if self.details['notes'] and 'Will also meet' in self.details['notes']:
			info = '[%d%d] %s (%s %d | %d %d):\n\t%s\n\t%s %s' % (
				self.details['year'], self.details['sem'], self.details['type'][0], '/'.join(self.details['depts']), self.details['num'], self.details['clbid'], self.details['crsid'],
				self.details['notes'],
				self.details['times'], self.details['places']
			)

			# get the timestring and location string out of the notes field
			notes_into_time_and_location_regex = r'.*meet ([MTWF][/-]?.*) in (.*)\.'
			results = re.search(notes_into_time_and_location_regex, self.details['notes'])
			extra_times, extra_locations = results.groups()
			# print(info + '\n\t' + 'regex matches:', [extra_times, extra_locations])
			print(extra_times)

			# split_time_regex =

			split_location_regex = r'(\w+ ?\d+)(?: or ?(\w+ ?\d+))?'

			# expandedDays = {
			# 	'M':  'Mo',
			# 	'T':  'Tu',
			# 	'W':  'We',
			# 	'Th': 'Th',
			# 	'F':  'Fr'
			# }

			# listOfDays = []

			# if '-' in daystring:
			# 	# M-F, M-Th, T-F
			# 	sequence = ['M', 'T', 'W', 'Th', 'F']
			# 	startDay = daystring.split('-')[0]
			# 	endDay = daystring.split('-')[1]
			# 	listOfDays = sequence.slice(
			# 		sequence.indexOf(startDay),
			# 		sequence.indexOf(endDay) + 1
			# 	)
			# else:
			# 	# MTThFW
			# 	spacedOutDays = daystring.replace(/([a-z]*)([A-Z])/g, '$1 $2')
			# 	# The regex sticks an extra space at the front. trim() it.
			# 	spacedOutDays = spacedOutDays.trim()
			# 	listOfDays = spacedOutDays.split(' ')

			# # 'M' => 'Mo'
			# return list(map(lambda day: expandedDays[day], listOfDays))

	def process(self):
		if self.output_type == 'csv':
			self.details = OrderedDict(sorted(self.details.items()))
		else:
			if self.details.get('title') == self.details.get('name'):
				del self.details['name']
			if (not self.details.get('title')) and (self.details.get('name')):
				self.details['title'] = self.details['name']
			cleanedcourse = {key: value for key, value in self.details.items() if value is not None}
			self.details = OrderedDict(sorted(cleanedcourse.items()))

	def save(self):
		if not dry_run:
			json_course_data = json.dumps(self.details, indent='\t', separators=(',', ': ')) + '\n'
			save_data(json_course_data, self.course_path)


########
# Utilities
######

def parse_links_for_text(string_with_links):
	return [link.get_text() for link in BeautifulSoup(string_with_links).find_all('a')]


def parse_paragraph_as_list(string_with_br):
	return [item for item in BeautifulSoup(string_with_br).strings]


def ensure_dir_exists(folder):
	# Make sure that a folder exists.
	d = os.path.dirname(folder)
	os.makedirs(d, exist_ok=True)


def load_data_from_file(filename):
	with open(filename, 'r') as infile:
		content = infile.read()
		return content


def find_details_subdir(clbid):
	n_thousand = int(int(clbid) / 1000)
	thousands_subdir = (n_thousand * 1000)
	return str(thousands_subdir).zfill(5) + '/' + str(clbid)


def save_data(data, filepath):
	ensure_dir_exists(filepath)
	filename = os.path.split(filepath)[1]
	with open(filepath, mode='w+', newline='\n') as outfile:
		outfile.write(data)

	# if not quiet: print('Wrote', filename, 'term data; %d bytes.' % (len(data)))


def delete_file(path):
	os.remove(path)
	if not quiet: print('Deleted', path)


def save_data_as_csv(data, filepath):
	ensure_dir_exists(filepath)
	filename = os.path.split(filepath)[1]
	with open(filepath, 'w+') as outfile:
		csv_file = csv.DictWriter(outfile, data[0].keys())
		csv_file.writeheader()
		csv_file.writerows(data)

	if not quiet: print('Wrote', filename, 'term data; %d bytes.' % (len(data)))


########
# Calculations
######

def year_plus_term(year, term):
	return int(str(year) + str(term))


def find_terms(start_year=None, end_year=None, this_year=False):
	start_year    = start_year if start_year else 1994
	current_year  = end_year if end_year else datetime.now().year
	current_month = datetime.now().month

	if this_year:
		start_year = current_year - 1 if current_month <= 7 else current_year

	most_years    = [year for year in range(start_year, current_year)]
	all_terms     = [1, 2, 3, 4, 5]
	limited_terms = [1, 2, 3]

	# Create a list of numbers like 20081 by concatenating the year and term
	# from 2008 to the year before this one.
	term_list = [year_plus_term(year, term) for year in most_years for term in all_terms]

	# St. Olaf publishes initial Fall, Interim, and Spring data in April of each year.
	# Full data is published by August.
	if start_year is not current_year or start_year is end_year:
		if current_month <= 3:
			current_year += 0
		elif 4 <= current_month <= 7:
			term_list += [year_plus_term(current_year, term) for term in limited_terms]
		else:
			term_list += [year_plus_term(current_year, term) for term in all_terms]
	else:
		term_list += [year_plus_term(current_year, term) for term in all_terms]

	# Sort the list of terms to 20081, 20082, 20091 (instead of 20081, 20091, 20082)
	# (sorts in-place)
	term_list.sort()

	return term_list


class Year:
	def __init__(self, year, terms, args=None):
		self.terms = terms[year]
		self.year = year
		self.args = args
		self.termdata = []
		self.completed = False

	def process(self):
		mapped_term_processor = functools.partial(Term, args=self.args)
		if not self.args.single_thread:
			with ProcessPoolExecutor(max_workers=5) as pool:
				self.termdata = list(pool.map(mapped_term_processor, self.terms))
		else:
			self.termdata = list(map(mapped_term_processor, self.terms))

	def get_terms(self):
		return str(self.year) + str([int(str(term)[4]) for term in self.terms])


def _flatten(l, fn, val=None):
	if not val: val = []
	if type(l) != list:
		return fn(l)
	if len(l) == 0:
		return fn(val)
	return [lambda x: _flatten(l[0], lambda y: _flatten(l[1:],fn,y), x), val]


def flattened(l):
	# from http://caolanmcmahon.com/posts/flatten_for_python/
	result = _flatten(l, lambda x: x)
	while type(result) == list and len(result) and callable(result[0]):
		if result[1] != []:
			yield result[1]
		result = result[0]([])
	yield result


def calculate_terms(terms, years):
	terms = terms or []
	years = years or []
	calculated_terms = []
	if not terms and not years:
		calculated_terms = find_terms()
	elif 0 in years:
		calculated_terms = find_terms(this_year=True)
	else:
		calculated_terms = terms + [find_terms(start_year=year, end_year=year) for year in years]
	return flattened(calculated_terms)


def pretty(lst):
	return ', '.join(lst)


def parse_year_from_filename(filename):
	# ex: 19943.json -> 1994
	return int(filename[0:4])


def json_folder_map(folder, kind):
	output = {
		'files': [],
		'type': kind
	}

	files = os.listdir(folder)
	for filename in files:
		if filename == '.DS_Store':
			continue
		path = folder + '/' + filename
		with open(path, 'rb') as infile:
			info = {
				'path': 'terms/' + filename,
				'hash': hashlib.sha1(infile.read()).hexdigest(),
				'year': parse_year_from_filename(filename)
			}
			output['files'].append(OrderedDict(sorted(info.items())))

	output['files'] = sorted(output['files'], key=lambda item: item['path'])

	output = OrderedDict(sorted(output.items()))

	if not dry_run:
		with open(info_path, 'w') as outfile:
			outfile.write(json.dumps(output, indent='\t', separators=(',', ': ')))
			outfile.write('\n')

	if not quiet: print('Hashed files; wrote info.json')


def maintain_lists_of_entries(all_courses):
	entry_list_path = mappings_path

	data_sets = {
		'departments': [],
		'professors': [],
		'times': [],
		'locations': [],
		'gereqs': [],
		'types': [],
	}

	for set_name, set_data in data_sets.items():
		filename = entry_list_path + 'valid_' + set_name + '.json'
		data = load_data_from_file(filename)
		data_sets[set_name] = json.loads(data)[set_name]

	for course in all_courses:
		data_sets['departments'].extend(course.get('depts') or [])
		data_sets['professors'].extend(course.get('profs') or [])
		data_sets['times'].extend(course.get('times') or [])
		data_sets['locations'].extend(course.get('places') or [])
		data_sets['gereqs'].extend(course.get('gereqs') or [])
		data_sets['types'].append(course.get('type') or [])

	data_sets['departments'] = sorted(set(data_sets['departments']))
	data_sets['professors'] = sorted(set(data_sets['professors']))
	data_sets['times'] = sorted(set(data_sets['times']))
	data_sets['locations'] = sorted(set(data_sets['locations']))
	data_sets['gereqs'] = sorted(set(data_sets['gereqs']))
	data_sets['types'] = sorted(set(data_sets['types']))


	for set_name, set_data in data_sets.items():
		filename = entry_list_path + 'valid_' + set_name + '.json'
		json_data = json.dumps({set_name: set_data}, indent='\t', separators=(',', ': '))
		if not dry_run:
			save_data(json_data, filename)


def main():
	global quiet
	global dry_run

	argparser = ArgumentParser(description='Fetch term data from the SIS.')

	argparser.add_argument('--terms', '-t',
		type=int, nargs='*',
		help='Terms for which to request data from the SIS.')

	argparser.add_argument('--years', '-y',
		type=int, nargs='*',
		help='Entire years for which to request data from the SIS.')

	argparser.add_argument('--force', '-f',
		action='store_true',
		help='Force reloading of the specified course.')

	argparser.add_argument('--dry', '-d',
		action='store_true',
		help='Only print output; don\'t write files.')

	argparser.add_argument('--single-thread', '-s',
		action='store_true',
		help='Only run with one thread; also returns useful debugging info')

	argparser.add_argument('--quiet', '-q',
		action='store_true',
		help='Silence logging; mostly used when looking for data.')

	argparser.add_argument('--output-type',
		type=str, nargs='?', choices=['json', 'csv'],
		help='Sets the output filetype.')

	args = argparser.parse_args()
	quiet = args.quiet
	dry_run = args.dry

	# Create an amalgamation of single terms and entire years as terms
	terms = calculate_terms(terms=args.terms, years=args.years)
	terms_grouped_by_years = {}
	for key, group in itertools.groupby(terms, lambda term: int(str(term)[0:4])):
		terms_grouped_by_years[key] = list(group)

	# Fire up the Terms
	mapped_year_processor = functools.partial(Year, args=args, terms=terms_grouped_by_years)
	years = list(map(mapped_year_processor, terms_grouped_by_years))
	if not quiet: print('Terms:', pretty([year.get_terms() for year in years]))

	[year.process() for year in years]

	json_folder_map(folder=term_dest, kind='courses')

	all_courses = [course for year in years for term in year.termdata for course in term.courses]
	maintain_lists_of_entries(all_courses)


if __name__ == '__main__':
	main()
