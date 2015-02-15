from .parse_links_for_text import parse_links_for_text

def split_and_flip_instructors(course):
	# Take a string like 'Bridges IV, William H.' and split/flip it
	# to 'William H. Bridges IV'. Oh, and do that for each professor.

	if 'instructors' in course:
		instructors = parse_links_for_text(course['instructors'])
		flipped_profs = []

		for prof in instructors:
			string_to_split = prof.split(',')
			actual_name = ''

			for name_part in reversed(string_to_split):
				name_part = name_part.strip()
				actual_name += name_part + ' '

			flipped_profs.append(actual_name.strip())

		return flipped_profs

	return course.get('instructors', [])
