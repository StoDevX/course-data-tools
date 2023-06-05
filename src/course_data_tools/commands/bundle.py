#!/usr/bin/env python3

from concurrent.futures import ProcessPoolExecutor
import functools
import os
import pathlib
from typing import Collection

import click
from structlog.stdlib import get_logger

from course_data_tools.json_folder_map import json_folder_map
from course_data_tools.calculate_terms import calculate_terms
from course_data_tools.regress_course import regress_course
from course_data_tools.load_courses import load_some_courses
from course_data_tools.save_term import save_term
from course_data_tools.paths import COURSE_DATA
from course_data_tools.paths import term_clbid_mapping_path


logger = get_logger()


def list_all_course_index_files():
    for file in os.listdir(term_clbid_mapping_path):
        if file.startswith("."):
            continue
        yield int(file.split(".")[0])


def one_term(term, *, legacy: bool, format: Collection[str], out_dir: pathlib.Path):
    log = logger.bind(term=f"{str(term)[:4]}:{str(term)[4]}")

    log.info("loading courses")
    courses = list(load_some_courses(term))

    if legacy:
        [regress_course(c) for c in courses]

    log.info("saving term data")
    for f in format:
        save_term(term, courses, kind=f, root_path=out_dir)


@click.command(help="Bundle SIS term data.")
@click.argument("term_or_year", nargs=-1)
@click.option(
    "-w",
    "--workers",
    help="The number of operations to perform in parallel",
    default=min(os.cpu_count() or 1, 4),
    show_default=True,
)
@click.option(
    "--legacy/--no-legacy",
    default=False,
    help="Use legacy mode (you don't need this)",
)
@click.option(
    "--out-dir",
    default=COURSE_DATA,
    type=click.Path(),
    help="Where to put info.json and terms/",
    show_default=True,
)
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "xml"], case_sensitive=False),
    multiple=True,
    default=["json"],
    show_default=True,
    help="Change the output format",
)
def bundle(*, term_or_year, workers, legacy, out_dir, format):
    """Terms (or entire years) for which to request data from the SIS"""

    if term_or_year:
        terms = calculate_terms(term_or_year)
    else:
        terms = list_all_course_index_files()

    edit_one_term = functools.partial(
        one_term,
        legacy=legacy,
        format=format,
        out_dir=out_dir,
    )

    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            list(pool.map(edit_one_term, terms))
    else:
        list(map(edit_one_term, terms))

    json_folder_map(root=out_dir, folder="terms", name="info")
