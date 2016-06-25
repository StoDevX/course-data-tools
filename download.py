#!/usr/bin/env python3

from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from argparse import ArgumentParser
import functools

from lib.fetch_course_details import fetch_course_details
from lib.calculate_terms import calculate_terms
from lib.process_courses import process_courses
from lib.fetch_term_data import load_term
from lib.log import log


def one_term(args, term):
    str_term = str(term)
    pretty_term = str_term[0:4] + ':' + str_term[4]

    log(pretty_term, 'Loading term')
    raw_term_data = load_term(term,
                              force_download=args.force_download_terms)

    if not raw_term_data:
        return []

    log(pretty_term, 'Extracting courses')
    courses = raw_term_data['searchresults']['course']

    log(pretty_term, 'Loading details')
    clbids = [c['clbid'] for c in courses]
    details = fetch_course_details(clbids,
                                   dry_run=args.dry_run,
                                   force_download=args.force_download_details)

    log(pretty_term, 'Processing courses')
    process_courses(courses, details,
                    dry_run=args.dry_run,
                    find_revisions=args.find_revisions,
                    ignore_revisions=args.ignore_revisions)


def run(args):
    terms = calculate_terms(args.term_or_year)
    edit_one_term = functools.partial(one_term, args)

    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(edit_one_term, terms))
    else:
        list(map(edit_one_term, terms))


def main():
    argparser = ArgumentParser(description='Fetch term data from the SIS.')
    argparser.allow_abbrev = False

    argparser.add_argument('term_or_year',
                           type=int,
                           nargs='*',
                           help='Terms (or entire years) for which to request data from the SIS.')
    argparser.add_argument('--workers', '-w',
                           type=int,
                           default=cpu_count(),
                           help='Control the number of operations to perform in parallel')
    argparser.add_argument('--force-terms',
                           action='store_true',
                           help='Force reloading of all specified terms.')
    argparser.add_argument('--force-details',
                           action='store_true',
                           help='Force reloading of course details from all specified terms.')
    argparser.add_argument('--dry-run', '-d',
                           action='store_true',
                           help='Only print output; don\'t write files.')
    argparser.add_argument('--no-revisions', '-n',
                           action='store_false',
                           help='Prevent searching for revisions of courses.')
    argparser.add_argument('--ignore-revisions',
                           metavar='PROP',
                           nargs='+',
                           default=[],
                           help='Prevent storing revisions within property $PROP.')
    argparser.add_argument('--quiet', '-q',
                           action='store_true',
                           help='Silence logging; mostly used when looking for data.')
    argparser.add_argument('--output-type',
                           action='store',
                           default='json',
                           choices=['json', 'csv'],
                           help='Change the output filetype.')

    args = argparser.parse_args()
    args.find_revisions = args.no_revisions

    run(args)


if __name__ == '__main__':
    main()
