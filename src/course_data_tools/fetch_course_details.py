import html
import json
import re

import requests_cache
from ratelimit import limits, sleep_and_retry
import sqlite_utils
from structlog.stdlib import get_logger

logger = get_logger()

apology = "Sorry, no description is available for this course."

bad_endings = [
    "Click on course title in the Class & Lab for more information about the course for that term.",
    "For more information on this course please see the following website: http://www.stolaf.edu/depts/english/courses/",
]

bad_beginnings = []

html_regex = re.compile(r"<[^>]*>")


@sleep_and_retry
@limits(calls=1, period=1)
def rate_limit():
    pass


def get_details(
    session: requests_cache.CachedSession,
    clbid: str,
    detail_cache: sqlite_utils.db.Table,
):
    body = ""

    try:
        if cached_body := detail_cache.get(clbid):
            body = cached_body["body"]
    except sqlite_utils.db.NotFoundError:
        pass

    if not body:
        url = f"https://sis.stolaf.edu/sis/public-coursedesc-json.cfm?clbid={clbid}"

        if not session.cache.has_url(url):
            rate_limit()

        # logger.debug("fetching %s", url)
        response = session.get(url)
        response.raise_for_status()

        body = response.text

        detail_cache.upsert(
            pk="clbid",  # type: ignore
            record=dict(clbid=clbid, body=body),
        )

    soup = clean_markup(clbid, body)
    cleaned = clean_details(soup)

    return cleaned


def clean_markup(clbid: str, raw_data: str) -> dict:
    start_str = "<!-- content:start -->"
    end_str = "<!-- content:end -->"

    try:
        start_idx = raw_data.index(start_str) + len(start_str)
        end_idx = raw_data.index(end_str)

        extracted_data = raw_data[start_idx:end_idx]
        data = json.loads(extracted_data)

        if len(data) == 0:
            raise Exception(f"zero results! {extracted_data}")
        elif len(data) > 1:
            raise Exception(f"more than one result! {extracted_data}")
    except ValueError:
        data = {clbid: {"description": None}}

    return next(iter(data.values()))


def sanitize_for_unicode(string: str):
    """Remove html entities"""
    return (
        html.unescape(string)
        .replace("\u0091", "‘")
        .replace("\u0092", "’")
        .replace("\u0093", "“")
        .replace("\u0094", "”")
        .replace("\u0096", "–")
        .replace("\u0097", "—")
        .replace("\u00ad", "-")
        .replace("\u00ae", "®")
    )


def clean_details(data: dict) -> dict:
    title = data.get("fullname")
    description = data.get("description")

    if title:
        title = sanitize_for_unicode(title)
        # Remove extra spaces from the string
        title = " ".join(title.split())
        # Remove the course time info from the end
        title = title.split("(", maxsplit=1)[0]
        # FIXME: use this
        # title = re.sub(r'(.*)\(.*\)$', r'\1', title)
        # Clean any extra whitespace off the title
        title = title.strip()
        # Remove html tags from the title
        title = html_regex.sub("", title)

    if description:
        # Collect the paragraphs into a list of strings
        full_description = {}
        paragraph_index = 0
        for part in description:
            if not part:
                paragraph_index += 1
                continue
            full_description[
                paragraph_index
            ] = f'{full_description.get(paragraph_index, "")} {part}'

        # Remove any remaining HTML tags
        description = [html_regex.sub("", para) for para in full_description.values()]

        # Remove extra spaces
        description = [" ".join(para.split()) for para in description]

        # Unescape any html entities
        # description = [html.unescape(para) for para in description]

        # Remove silly endings and beginnings
        for ending in bad_endings:
            description = [
                " ".join(para.split(ending)) if ending in para else para
                for para in description
            ]
        for beginning in bad_beginnings:
            description = [
                " ".join(para.split(beginning)) if beginning in para else para
                for para in description
            ]

        # Clean any extra whitespace off the description
        description = [para.strip() for para in description]

        # Remove any blank strings
        description = [sanitize_for_unicode(para) for para in description if para]

    if not description or description == [apology] or description == [title]:
        description = None

    if not title:
        title = None

    return {"title": title, "description": description}
