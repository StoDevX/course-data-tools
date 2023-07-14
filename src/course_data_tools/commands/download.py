from typing import cast
import requests_cache
import sqlite_utils
import typer
from structlog.contextvars import bind_contextvars
from structlog.stdlib import get_logger
from rich.progress import track

from course_data_tools.fetch_course_details import (
    get_details,
)
from course_data_tools.fetch_term_data import load_term
from course_data_tools.process_courses import process_course as process_course_section

logger = get_logger()
app = typer.Typer()


def download_term(
    term: str,
    *,
    session: requests_cache.CachedSession,
    db: sqlite_utils.Database,
    cache: sqlite_utils.Database,
):
    bind_contextvars(term=term)

    logger.info("processing term")

    term_cache = cast(sqlite_utils.db.Table, cache["term"])
    detail_cache = cast(sqlite_utils.db.Table, cache["detail"])

    section = cast(sqlite_utils.db.Table, db.table("section"))
    allowed_keys = set(section.columns_dict.keys())

    for course in track(load_term(session, term=term, term_cache=term_cache)):
        clbid = course["clbid"]
        bind_contextvars(clbid=clbid)

        details = get_details(session, clbid=clbid, detail_cache=detail_cache)
        course = process_course_section(course, details, term=term)

        section.upsert(
            {k: v for k, v in course.items() if k in allowed_keys},
            pk="clbid",  # type: ignore
        )

    sections_for_term = section.count_where("term = :term", {"term": term})
    logger.info(f"downloaded {sections_for_term:,} course sections")
