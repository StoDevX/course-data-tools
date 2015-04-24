from argparse import ArgumentParser
from .flattened import flatten
from .find_terms import find_terms


def calculate_terms(terms, years):
    terms = terms or []
    years = years or []

    if (not terms) and (not years):
        calculated_terms = find_terms()
    elif 0 in years:
        calculated_terms = find_terms(this_year=True)
    else:
        calculated_terms = terms + \
            [find_terms(start_year=year, end_year=year) for year in years]

    return flatten(calculated_terms)


if __name__ == '__main__':
    argparser = ArgumentParser()
    argparser.add_argument('--terms', type=int, nargs='*')
    argparser.add_argument('--years', type=int, nargs='*')
    args = argparser.parse_args()

    terms = map(str, calculate_terms(terms=args.terms, years=args.years))
    if terms:
        print(' '.join(terms))
