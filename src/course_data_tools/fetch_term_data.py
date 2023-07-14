import re
import urllib.parse

import requests
import sqlite_utils
import xmltodict
from ratelimit import limits, sleep_and_retry
from structlog.stdlib import get_logger

logger = get_logger()


def fix_invalid_xml(raw):
    """Replace any invalid XML entities with &amp;"""
    return re.sub(r"&(?!(?:[a-z]+|#[0-9]+|#x[0-9a-f]+);)", "&amp;", raw)


@sleep_and_retry
@limits(calls=1, period=1)
def build_term_url(term: str) -> str:
    if "-" in term:
        year, term = term.split("-")
        term = f"{year}{term}"
    base_url = "https://sis.stolaf.edu/sis/public-acl-inez.cfm"
    querystring = urllib.parse.urlencode({"searchyearterm": str(term)})
    return f"{base_url}?{querystring}"


def build_static_term_url(term: str) -> str:
    if "-" in term:
        year, term = term.split("-")
        term = f"{year}{term}"
    return f"https://sis.stolaf.edu/sis/static-classlab/{term}.xml"


def get(session: requests.Session, url: str) -> requests.Response:
    try:
        r = session.get(url)
        r.raise_for_status()
        return r

    except requests.HTTPError as err:
        response: requests.Response = err.response
        body = err.response.text

        server_error_msg = "Sorry, there's been an error"
        if server_error_msg in body:
            raise requests.HTTPError(
                "Server Error: %s for url: %s",
                server_error_msg,
                response.url,
            )

        timeout_exceeded_msg = "The request has exceeded the allowable time limit"
        if timeout_exceeded_msg in body:
            raise requests.HTTPError(
                "Server Timeout Error: %s for url: %s",
                timeout_exceeded_msg,
                response.url,
            )

        raise err


def get_xml_body(
    session: requests.Session,
    url: str,
) -> str:
    try:
        body = get(session, url).text
        # remove the coldfusion debugging output
        end_str = "</searchresults>"
        end_idx = body.index(end_str) + len(end_str)
        return body[:end_idx]
    except ValueError:
        raise ValueError(f"{url} did not return any xml")


def fetch_term(session: requests.Session, term: str) -> str:
    try:
        static_data_url = build_static_term_url(term)
        return get_xml_body(session, static_data_url)
    except requests.HTTPError as exception:
        if exception.response.status_code != 404:
            raise exception

        url = build_term_url(term)
        return get_xml_body(session, url)


def load_term(
    session: requests.Session,
    *,
    term: str,
    term_cache: sqlite_utils.db.Table,
) -> list[dict]:
    body = ""

    try:
        if cached_body := term_cache.get(term):
            body = cached_body["body"]
    except sqlite_utils.db.NotFoundError:
        pass

    if not body:
        body = fetch_term(session, term)

        term_cache.upsert(
            pk="term",  # type: ignore
            record=dict(term=term, body=body),
        )

    body = fix_invalid_xml(body)

    parsed = xmltodict.parse(body, force_list=["course"])

    search_results = parsed["searchresults"] or {}

    return search_results.get("course", [])
