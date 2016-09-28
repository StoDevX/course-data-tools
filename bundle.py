#!/usr/bin/env python3

from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from argparse import ArgumentParser
import functools
import os

from lib.json_folder_map import json_folder_map
from lib.calculate_terms import calculate_terms
from lib.regress_course import regress_course
from lib.load_courses import load_some_courses
from lib.save_term import save_term
from lib.paths import COURSE_DATA
from lib.log import log
from lib.paths import term_clbid_mapping_path


def list_all_course_index_files():
    for file in os.listdir(term_clbid_mapping_path):
        if file.startswith('.'):
            continue
        yield int(file.split('.')[0])


def one_term(args, term):
    str_term = str(term)
    pretty_term = '{}:{}'.format(str_term[0:4], str_term[4])

    log(pretty_term, 'Loading courses')
    courses = list(load_some_courses(term))

    if args.legacy:
      for c in courses:
        regress_course(c)

    log(pretty_term, 'Saving term')
    for f in args.format:
        save_term(term, courses, kind=f, root_path=args.out_dir)


def run(args):
    if args.term_or_year:
        terms = calculate_terms(args.term_or_year)
    else:
        terms = list_all_course_index_files()
    edit_one_term = functools.partial(one_term, args)

    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(edit_one_term, terms))
    else:
        list(map(edit_one_term, terms))

    json_folder_map(root=args.out_dir, folder='terms', name='index' if not args.legacy else 'legacy')


def main():
    argparser = ArgumentParser(description='Bundle SIS term data.')
    argparser.allow_abbrev = False

    argparser.add_argument('term_or_year',
                           type=int,
                           nargs='*',
                           help='Terms (or entire years) for which to request data from the SIS')
    argparser.add_argument('-w',
                           metavar='WORKERS',
                           type=int,
                           default=cpu_count(),
                           help='The number of operations to perform in parallel')
    argparser.add_argument('--legacy',
                           action='store_true',
                           help="Use legacy mode (you don't need this)")
    argparser.add_argument('--out-dir',
                           nargs='?',
                           action='store',
                           default=COURSE_DATA,
                           help='Where to put info.json and terms/')
    argparser.add_argument('--format',
                           action='append',
                           nargs='?',
                           choices=['json', 'csv', 'xml'],
                           help='Change the output filetype')

    args = argparser.parse_args()
    args.format = ['json'] if not args.format else args.format

    run(args)


if __name__ == '__main__':
    main()
