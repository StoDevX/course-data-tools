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

from data_processing.lib.maintain_lists_of_entries import maintain_lists_of_entries
from data_processing.lib.calculate_terms import calculate_terms
from data_processing.lib.json_folder_map import json_folder_map
from data_processing.lib.pretty import pretty
from data_processing.Year import Year

from data_processing.lib.paths import handmade_path

quiet = False
dry_run = False

departments = None
with open(handmade_path + 'to_department_abbreviations.json') as depts:
	departments = json.loads(depts.read())

course_types = None
with open(handmade_path + 'course_types.json') as types:
	course_types = json.loads(types.read())

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

# get data
# process data
# maintain lists
# generate final files
