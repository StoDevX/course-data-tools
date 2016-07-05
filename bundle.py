#!/usr/bin/env python3

from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from argparse import ArgumentParser
import functools

from lib.json_folder_map import json_folder_map
from lib.calculate_terms import calculate_terms
from lib.load_courses import load_some_courses
from lib.save_term import save_term
from lib.paths import term_dest
from lib.log import log


def one_term(args, term):
    str_term = str(term)
    pretty_term = '{}:{}'.format(str_term[0:4], str_term[4])

    log(pretty_term, 'Loading courses')
    courses = load_some_courses(term)

    log(pretty_term, 'Saving term')
    for f in args.format:
        save_term(term, courses, kind=f)


def run(args):
    terms = calculate_terms(args.term_or_year)
    edit_one_term = functools.partial(one_term, args)

    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(edit_one_term, terms))
    else:
        list(map(edit_one_term, terms))

    json_folder_map(folder=term_dest, path=term_dest)


def main():
    argparser = ArgumentParser(description='Bundle SIS term data.')
    argparser.allow_abbrev = False

    argparser.add_argument('term_or_year',
                           type=int,
                           nargs='*',
                           help='Terms (or entire years) for which to request data from the SIS')
    argparser.add_argument('--workers', '-w',
                           type=int,
                           default=cpu_count(),
                           help='Control the number of operations to perform in parallel')
    argparser.add_argument('--format',
                           action='store',
                           nargs='+',
                           default='json',
                           choices=['json', 'csv', 'xml'],
                           help='Change the output filetype')

    run(argparser.parse_args())


if __name__ == '__main__':
    main()
