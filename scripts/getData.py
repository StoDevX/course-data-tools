#!/usr/bin/env python3

from concurrent.futures import ProcessPoolExecutor
from argparse import ArgumentParser
import functools

from lib.fetch_course_details import fetch_course_details
from lib.calculate_terms import calculate_terms
from lib.process_courses import process_courses
from lib.fetch_term_data import load_term
from lib.flattened import flatten
from lib.log import log


def get_years_and_terms(terms_or_years):
	years, terms = [], []
	for item in terms_or_years:
		str_item = str(item)
		if len(str_item) is 4:
			years.append(item)
		elif len(str_item) is 5:
			terms.append(item)

	return years, terms


def get_args():
	argparser = ArgumentParser(description='Fetch term data from the SIS.')

	argparser.add_argument('term_or_year', type=int, nargs='*', help='Terms (or entire years) for which to request data from the SIS.')
	argparser.add_argument('--workers', '-w', type=int, default=8, help='Specify the number of terms to run simultaneously.')
	argparser.add_argument('--force-download-terms', action='store_true', help='Force reloading of the specified terms.')
	argparser.add_argument('--force-download-details', action='store_true', help='Force reloading of any course details from the specified terms.')
	argparser.add_argument('--dry-run', '-d', action='store_true', help='Only print output; don\'t write files.')
	argparser.add_argument('--no-revisions', '-n', action='store_false', help='Prevent searching for revisions of courses.')
	argparser.add_argument('--quiet', '-q', action='store_true', help='Silence logging; mostly used when looking for data.')

	return argparser.parse_args()


def one_term(term, workers, **kwargs):
	str_term = str(term)
	pretty_term = str_term[0:4] + ':' + str_term[4]

	log(pretty_term, 'Loading term')
	raw_term_data = load_term(term,
		force_download=kwargs['force_download_terms'])

	if not raw_term_data:
		return []

	log(pretty_term, 'Extracting courses')
	courses = raw_term_data['searchresults']['course']

	log(pretty_term, 'Loading details')
	details = fetch_course_details([c['clbid'] for c in courses],
		dry_run=kwargs['dry_run'], force_download=kwargs['force_download_details'])

	log(pretty_term, 'Processing courses')
	final_courses = process_courses(courses, details,
		dry_run=kwargs['dry_run'], find_revisions=kwargs['find_revisions'])

	return final_courses


def main():
	args = get_args()
	years, terms = get_years_and_terms(args.term_or_year)

	terms = calculate_terms(years=years, terms=terms)

	edit_one_term = functools.partial(one_term, find_revisions=args.no_revisions, **vars(args))

	if args.workers > 1:
		with ProcessPoolExecutor(max_workers=args.workers) as pool:
			courses = list(pool.map(edit_one_term, terms))
	else:
		courses = list(map(edit_one_term, terms))

	return terms


if __name__ == '__main__':
	main()

	# json_folder_map(folder=term_dest, kind='courses')

	# all_courses = [course for year in years for term in year.termdata for course in term.courses]
	# maintain_lists_of_entries(all_courses)
