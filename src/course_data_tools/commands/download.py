#!/usr/bin/env python3

import functools
import os
from concurrent.futures import ProcessPoolExecutor
from typing import Iterable

import click
from course_data_tools.calculate_terms import calculate_terms
from course_data_tools.fetch_course_details import fetch_course_details
from course_data_tools.fetch_term_data import load_term
from course_data_tools.process_courses import process_course
from course_data_tools.save_term_clbid_list import save_term_clbid_list
from structlog.stdlib import get_logger

logger = get_logger()


def one_term(
    term: str,
    *,
    force_terms: bool,
    dry_run: bool,
    force_details: bool,
    ignore_revision_keys: Iterable[str],
    no_revisions: bool,
):
    log = logger.bind(term=f"{str(term)[:4]}:{str(term)[4]}")

    log.info("processing term")
    clbids = []
    for course in load_term(term, force_download=force_terms):
        details = fetch_course_details(
            course["clbid"],
            dry_run=dry_run,
            force_download=force_details,
        )
        course = process_course(
            course,
            details,
            dry_run=dry_run,
            ignore_revision_keys=ignore_revision_keys,
            no_revisions=no_revisions,
        )
        clbids.append(course["clbid"])

    if not clbids:
        log.info("no classes found")
        return

    log.info("saving course map")
    # do it again: this time, we get the numeric versions
    save_term_clbid_list(term, clbids)


@click.command(help="Fetch term data from the SIS.")
@click.argument("term_or_year", nargs=-1)
@click.option(
    "-w",
    "--workers",
    help="The number of operations to perform in parallel",
    default=min(os.cpu_count() or 1, 4),
    show_default=True,
)
@click.option(
    "--force",
    default=False,
    help="Force download of all specified terms",
)
@click.option(
    "--force-details",
    default=False,
    help="Force download of course details from all specified terms",
)
@click.option(
    "-d",
    "--dry-run",
    default=False,
    help="Only print output; don't write files",
)
@click.option(
    "--ignore-revision-keys",
    type=str,
    multiple=True,
    help="Prevent storing revisions within the speficied keys",
)
@click.option("--no-revisions", default=False, help="Do not check for revisions at all")
def download(
    *,
    term_or_year: Iterable[str],
    workers: int,
    force: bool,
    force_details: bool,
    dry_run: bool,
    ignore_revision_keys: Iterable[str],
    no_revisions: bool,
):
    """Terms (or entire years) for which to request data from the SIS."""

    terms = calculate_terms(term_or_year)
    edit_one_term = functools.partial(
        one_term,
        force_terms=force,
        dry_run=dry_run,
        force_details=force_details,
        ignore_revision_keys=ignore_revision_keys,
        no_revisions=no_revisions,
    )

    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            list(pool.map(edit_one_term, terms))
    else:
        [edit_one_term(term) for term in terms]
