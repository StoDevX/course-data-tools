from argparse import ArgumentParser
from datetime import datetime
from .year_plus_term import year_plus_term

def find_terms_for_year(year):
	now = datetime.now()
	current_month = now.month
	current_year = now.year

	all_terms     = [1, 2, 3, 4, 5]
	limited_terms = [1, 2, 3]

	# St. Olaf publishes initial Fall, Interim, and Spring data in April of each year.
	# Full data is published by August.
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

	start_year    = start_year or 1994
	end_year      = end_year or now.year
	current_year  = end_year if end_year is not start_year else end_year + 1
	current_month = now.month

	if this_year:
		start_year = current_year - 1 if current_month <= 7 else current_year

	most_years = range(start_year, current_year)
	term_list  = list(map(find_terms_for_year, most_years))

	# Sort the list of terms to 20081, 20082, 20091 (instead of 20081, 20091, 20082)
	# (sorts in-place)
	term_list.sort()

	return term_list


if __name__ == '__main__':
	argparser = ArgumentParser()
	argparser.add_argument('--start-year', type=int, nargs=1)
	argparser.add_argument('--end-year',   type=int, nargs=1)
	argparser.add_argument('--this-year',  action='store_true')
	args = argparser.parse_args()

	terms = find_terms(
		start_year=args.start_year[0],
		end_year=args.end_year[0],
		this_year=args.this_year)
	terms = [str(term) for term in terms]
	print(' '.join(terms))
