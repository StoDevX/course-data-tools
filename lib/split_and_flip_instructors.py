from .parse_links_for_text import parse_links_for_text


def split_and_flip_instructors(instructors):
    # Take a string like 'Bridges IV, William H.' and split/flip it
    # to 'William H. Bridges IV'. Oh, and do that for each professor.

    flipped_profs = []

    for prof in parse_links_for_text(instructors):
        string_to_split = reversed(prof.split(','))
        actual_name = ' '.join([name_part.strip() for name_part in string_to_split])
        flipped_profs.append(actual_name.strip())

    return flipped_profs
