#!/usr/bin/env python3

from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from argparse import ArgumentParser
import functools

from lib.save_term_clbid_list import save_term_clbid_list
from lib.fetch_course_details import fetch_course_details
from lib.calculate_terms import calculate_terms
from lib.process_courses import process_course
from lib.fetch_term_data import load_term


def one_term(args, term):
    pretty_term = f'{str(term)[:4]}:{str(term)[4]}'

    clbids = []
    print(pretty_term, 'Processing term')
    for course in load_term(term, force_download=args.force_terms):
        details = fetch_course_details(course['clbid'], dry_run=args.dry_run, force_download=args.force_details)
        course = process_course(course, details, dry_run=args.dry_run, ignore_revisions=args.ignore_revisions)
        clbids.append(course['clbid'])

    if not clbids:
        print(pretty_term, 'No classes found')
        return

    print(pretty_term, 'Saving course mapping')
    # do it again: this time, we get the numeric versions
    save_term_clbid_list(term, clbids)


def run(args):
    terms = calculate_terms(args.term_or_year)
    edit_one_term = functools.partial(one_term, args)

    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(edit_one_term, terms))
    else:
        [edit_one_term(term) for term in terms]


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
    argparser.add_argument('--ignore-revisions',
                           metavar='PROP',
                           nargs='+',
                           default=[],
                           help='Prevent storing revisions within property $PROP.')
    argparser.add_argument('--quiet', '-q',
                           action='store_true',
                           help='Silence logging; mostly used when looking for data.')

    args = argparser.parse_args()

    run(args)


if __name__ == '__main__':
    main()
