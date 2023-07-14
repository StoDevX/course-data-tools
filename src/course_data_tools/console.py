import enum
import pathlib
from typing import Annotated, cast

import appdirs
import typer
from requests_cache import CachedSession
from sqlite_utils import Database
from sqlite_utils.db import Table

from course_data_tools.commands.download import download_term

APP_NAME = "course-data-tools"

app = typer.Typer(name=APP_NAME)
USER_CACHE_DIR = pathlib.Path(appdirs.user_cache_dir(APP_NAME))

session: CachedSession
db: Database
cache: Database


class ForceMode(str, enum.Enum):
    none = "none"
    all = "all"
    terms = "terms"
    details = "details"


def cli():
    global session, db, cache
    session = CachedSession()
    USER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # db = Database(USER_CACHE_DIR / "data.sqlite3")
    db = Database("./course-data.sqlite3")

    section = cast(Table, db.table("section"))
    section.create(
        if_not_exists=True,
        pk="clbid",
        columns=dict(
            clbid=int,
            credits=float,
            crsid=str,
            department=str,
            description=str,
            enrolled=int,
            firstyear=int,
            gereqs=list,
            groupid=str,
            grouptype=str,
            instructors=list,
            junior=int,
            learningmode=str,
            level=int,
            max=int,
            name=str,
            notes=str,
            number=str,
            offerings=list,
            pn=bool,
            prerequisites=str,
            section=str,
            semester=int,
            senior=int,
            sophomore=int,
            status=str,
            term=str,
            title=str,
            type=str,
            year=int,
        ),
    )

    cache = Database("./cache.sqlite3")

    term_cache = cast(Table, cache.table("term"))
    term_cache.create(
        if_not_exists=True,
        pk="term",
        columns=dict(term=str, body=str),
    )

    detail_cache = cast(Table, cache.table("detail"))
    detail_cache.create(
        if_not_exists=True,
        pk="clbid",
        columns=dict(clbid=str, body=str),
    )

    app()


@app.command()
def download(
    term: Annotated[str, typer.Argument(help="The term to download (e.g., 2023-1)")],
):
    """Downloads course section data for the given term from SIS."""
    download_term(term, session=session, db=db, cache=cache)


@app.command()
def bundle(
    term: Annotated[str, typer.Argument(help="The term to download (e.g., 2023-1)")],
):
    """Downloads course section data for the given term from SIS."""
    print(appdirs.user_cache_dir(app.info.name, "data.sqlite3"))

    # download_term(term, session=session, db=db)
