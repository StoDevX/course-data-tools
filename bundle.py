#!/usr/bin/env python3

from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from argparse import ArgumentParser
import functools
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from lib.json_folder_map import json_folder_map
from lib.calculate_terms import calculate_terms
from lib.regress_course import regress_course
from lib.load_courses import load_some_courses
from lib.save_term import save_term
from lib.paths import COURSE_DATA
from lib.log import log
from lib.paths import term_clbid_mapping_path
import lib.database_manual as db
import lib.database as orm


# import logging
#
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)


def list_all_course_index_files():
    for file in os.listdir(term_clbid_mapping_path):
        if file.startswith('.'):
            continue
        yield int(file.split('.')[0])


def one_term(args, term):
    pretty_term = f'{str(term)[:4]}:{str(term)[4]}'

    log(pretty_term, 'Loading courses')
    courses = list(load_some_courses(term))

    if args.legacy:
        [regress_course(c) for c in courses]

    log(pretty_term, 'Saving term')
    for f in args.format:
        save_term(term, courses, kind=f, root_path=args.out_dir)


def generate_sqlite_db_orm(args):
    if os.path.exists('../courses.db'):
        os.remove('../courses.db')
    # engine = create_engine('sqlite:///../courses.db', echo=True)
    engine = create_engine('sqlite:///../courses.db', echo=False)

    orm.Base.metadata.create_all(engine)
    make_session = sessionmaker(bind=engine)
    s = make_session()

    if args.term_or_year:
        terms = calculate_terms(args.term_or_year)
    else:
        terms = sorted(list_all_course_index_files())

    for term in terms:
        pretty_term = f'{str(term)[:4]}:{str(term)[4]}'
        print(pretty_term, 'Loading courses')
        courses = list(load_some_courses(term))
        print(pretty_term, 'Filling database')
        for c in courses:
            cleaned = orm.clean_course(c, s)
            s.add(cleaned)
        # cleaned = [orm.clean_course(c, s) for c in courses]
        # print(pretty_term, 'Saving term')
        # s.add_all(cleaned)

    print('Writing to disk')
    s.commit()


def query_sqlite_orm(args):
    if not os.path.exists('../courses.db'):
        print('missing database')
        return
    engine = create_engine('sqlite:///../courses.db', echo=True)
    # engine = create_engine('sqlite:///../courses.db', echo=False)

    orm.Base.metadata.create_all(engine)
    make_session = sessionmaker(bind=engine)
    s = make_session()

    # dept = s.query(orm.Department).filter(orm.Department.abbr == 'CSCI').first()

    # c = s.query(orm.Course, orm.Department)\
    #     .filter(orm.Course.year == 2012)\
    #     .filter(orm.Course.departments.in_([dept.id]))

    # print(c.first())

    print(s.query(orm.Course).filter(orm.Course.abbr.in_(['CSCI'])).first())


def query_sqlite_manual(args):
    if not os.path.exists('../courses.db'):
        print('missing database')
        return
    # engine = create_engine('sqlite:///../courses.db', echo=True)
    engine = create_engine('sqlite:///../courses.db', echo=False)
    conn = engine.connect()

    stmt = text("""
        SELECT 
          course.clbid, 
          department.abbr || ' ' || course.number || COALESCE(course.section, '') as deptnum,
          course.name, 
          course.year || '-' || course.semester as term
        FROM course
        LEFT JOIN courses_to_depts dept
            ON course.id = dept.course_id
          LEFT JOIN department
            ON department.id = dept.department_id 
        WHERE course.year = :year 
          AND department.abbr = :dept
          AND course.name NOT IN ('IR/', 'IS/', 'Academic Internship')
    """)

    stmt = stmt.bindparams(dept="CSCI", year=2016)

    print(stmt.compile(engine, compile_kwargs={"literal_binds": True}))

    for row in conn.execute(stmt).fetchall():
        print(dict(row))


def generate_sqlite_db(args):
    if os.path.exists('../courses.db'):
        os.remove('../courses.db')
    # engine = create_engine('sqlite:///../courses.db', echo=True)
    engine = create_engine('sqlite:///../courses.db', echo=False)

    db.metadata.create_all(engine)
    conn = engine.connect()

    if args.term_or_year:
        terms = calculate_terms(args.term_or_year)
    else:
        terms = sorted(list_all_course_index_files())

    for term in terms:
        pretty_term = f'{str(term)[:4]}:{str(term)[4]}'
        print(pretty_term, 'Loading courses')
        courses = list(load_some_courses(term))
        print(pretty_term, 'Saving term')
        cleaned = [db.clean_course(c) for c in courses]
        for c in cleaned:
            db.insert_course(c, conn)


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

    json_folder_map(root=args.out_dir, folder='terms', name='info')


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
                           dest='workers',
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
                           choices=['json', 'csv', 'xml', 'sqlite', 'orm', 'query-orm', 'query'],
                           help='Change the output filetype')

    args = argparser.parse_args()
    args.format = ['json'] if not args.format else args.format

    if 'sqlite' in args.format:
        generate_sqlite_db(args)
    elif 'orm' in args.format:
        generate_sqlite_db_orm(args)
    elif 'query-orm' in args.format:
        query_sqlite_orm(args)
    elif 'query' in args.format:
        query_sqlite_manual(args)
    else:
        run(args)


if __name__ == '__main__':
    main()
