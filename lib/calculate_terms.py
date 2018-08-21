from .flattened import flatten
from datetime import datetime


def year_plus_term(year, term):
    return int(str(year) + str(term))


def find_terms_for_year(year):
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    all_terms = [1, 2, 3, 4, 5]
    limited_terms = [1, 2, 3]

    # St. Olaf publishes initial Fall, Interim, and Spring data in April
    # of each year. Full data is published by August.
    if year == current_year:
        if current_month < 3:
            return []
        elif current_month <= 7:
            return [year_plus_term(year, term) for term in limited_terms]
        else:
            return [year_plus_term(year, term) for term in all_terms]

    elif year > current_year:
        return []

    else:
        return [year_plus_term(year, term) for term in all_terms]


def find_terms(start_year=None, end_year=None, this_year=False):
    now = datetime.now()

    start_year = start_year or 1994
    end_year = end_year or now.year
    current_year = end_year if end_year is not start_year else end_year + 1
    current_month = now.month

    if this_year:
        start_year = current_year - 1 if current_month <= 7 else current_year

    most_years = range(start_year, current_year)
    term_list = [find_terms_for_year(year) for year in most_years]

    # Sort the list of terms to 20081, 20082, 20091
    # (instead of 20081, 20091, 20082)
    term_list = sorted(term_list)

    return term_list


def get_years_and_terms(terms_and_years):
    terms_and_years = flatten([item.split(' ')
                               if type(item) is str
                               else item
                               for item in terms_and_years])

    years, terms = [], []
    for item in terms_and_years:
        str_item = str(item)
        if len(str_item) is 4:
            years.append(item)
        elif len(str_item) is 5:
            terms.append(item)

    return years, terms


def calculate_terms(terms_and_years):
    years, terms = get_years_and_terms(terms_and_years)

    if (not terms) and (not years):
        calculated_terms = find_terms()
    elif 0 in years:
        calculated_terms = find_terms(this_year=True)
    else:
        calculated_terms = terms + \
            [find_terms(start_year=year, end_year=year) for year in years]

    return flatten(calculated_terms)
