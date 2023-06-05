from .parse_links_for_text import parse_links_for_text


def flip_instructor(name):
    string_to_split = reversed(name.split(","))
    actual_name = " ".join([name_part.strip() for name_part in string_to_split])
    return actual_name.strip()


def split_and_flip_instructors(instructors):
    # Take a string like 'Bridges IV, William H.' and split/flip it
    # to 'William H. Bridges IV'. Oh, and do that for each professor.

    return [flip_instructor(name) for name in parse_links_for_text(instructors)]
