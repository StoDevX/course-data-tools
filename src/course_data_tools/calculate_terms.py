from typing import Iterable, Iterator
from datetime import date


def year_plus_term(year: str | int, term: str) -> str:
    return f"{year}-{term}"


def get_years_and_terms(terms_and_years: Iterable[str]) -> tuple[list[int], list[str]]:
    years, terms = [], []

    for group in terms_and_years:
        for item in group.split():
            match len(item):
                case 4:
                    years.append(item)
                case 5:
                    terms.append(year_plus_term(item[0:4], item[5]))
                case 6:
                    terms.append(item)

    return years, terms


def calculate_terms(terms_and_years: Iterable[str], now=date.today()) -> Iterator[str]:
    all_terms = ["1", "2", "3", "4", "5"]
    years, terms = get_years_and_terms(terms_and_years)

    yield from terms

    if not years and not terms:
        years = range(1994, now.year + 1)

    for year in years:
        for term in all_terms:
            yield year_plus_term(year, term)
