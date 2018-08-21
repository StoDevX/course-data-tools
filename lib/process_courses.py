import json
import re
import html
import logging
import os
from textwrap import dedent

from .check_for_course_revisions import check_for_revisions
from .data import course_types
from .parse_links_for_text import parse_links_for_text
from .parse_paragraph_as_list import parse_paragraph_as_list
from .paths import make_course_path
from .save_data import save_data
from .split_and_flip_instructors import split_and_flip_instructors
from .parse_timestring import parse_timestring
from .parse_prerequisites import parse_prerequisites
from .parse_notes import parse_notes


def json_date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError(f'Object of type {type(obj)} with value of {repr(obj)} is not JSON serializable')


def save_course(course):
    course_path = make_course_path(course['clbid'])
    json_course_data = json.dumps(course,
                                  indent='\t',
                                  default=json_date_handler,
                                  ensure_ascii=False,
                                  sort_keys=True) + '\n'
    save_data(json_course_data, course_path)


def check_for_course_file_existence(clbid):
    return os.path.exists(make_course_path(clbid))


def create_offerings(*, times, locations):
    if not times or not locations:
        return None

    o_times = times
    o_locations = locations

    if len(locations) == 1 and len(times) != len(locations):
        locations = [locations[0] for i in range(len(times))]

    if len(set(locations)) == 1:
        locations = [locations[0] for i in range(len(times))]

    if times and locations and len(times) != len(locations) and len(locations) != 1:
        raise UserWarning(f'Times ({len(times)}) and Locations ({len(locations)}) are different lengths in', {'times': times, 'locations': locations}, {'originals': [o_times, o_locations]})

    for time, loc in zip(times, locations):
        for parsed in parse_timestring(time):
            yield {
                'location': loc,
                'day': parsed['day'],
                'start': parsed['start'],
                'end': parsed['end'],
            }


def clean_course(course):
    # Unescape &amp; in course names
    course['name'] = html.unescape(course['coursename'])
    del course['coursename']

    course['section'] = course['coursesection']
    del course['coursesection']

    course['status'] = course['coursestatus']
    del course['coursestatus']

    # Remove <br> tags from the 'notes' field.
    if course['notes']:
        course['notes'] = course['notes'].split('<br>')
        course['notes'] = [' '.join(note.split()) for note in course['notes']]
        course['notes'] = [html.unescape(note) for note in course['notes']]
        course['notes'] = [note for note in course['notes'] if note]

    # Remove the unused varcredits property
    del course['varcredits']

    # Flesh out coursesubtype
    if course['coursesubtype'] and course['coursesubtype'] in course_types:
        course['type'] = course_types[course['coursesubtype']]
    else:
        course['type'] = course['coursesubtype']
        raise UserWarning(f"'{course['type']}' doesn't appear in the types list, in", course)
    del course['coursesubtype']

    # Break apart dept names into lists
    course['department'] = course['deptname']
    del course['deptname']

    # Turn numbers into numbers
    if re.search(r'\d{3}$', course['coursenumber']):
        course['number'] = int(course['coursenumber'])
    elif re.match(r'\dXX', course['coursenumber']):
        course['number'] = course['coursenumber']
    elif re.match(r'\d{3}I', course['coursenumber']):
        course['number'] = int(course['coursenumber'][:-1])
    else:
        course['number'] = course['coursenumber']
    del course['coursenumber']

    course['credits'] = float(course['credits'])

    course['enrolled'] = int(course['enroll'])
    del course['enroll']
    course['max'] = int(course['max'])

    # Turn booleans into booleans
    course['pn'] = True if course['pn'] is 'Y' else False

    # Add the term, year, and semester
    # `term` looks like 20083, where the first four digits represent the
    # year, and the last digit represents the semester
    course['term'] = int(course['term'])
    course['year'] = int(str(course['term'])[:4])  # Get the first four digits
    course['semester'] = int(str(course['term'])[4])   # Get the last digit

    # Add the course level
    if type(course['number']) is int:
        course['level'] = (course['number'] // 100) * 100
    elif course['number'] == 'XX':
        course['level'] = 0
    elif 'X' in course['number']:
        course['level'] = int(course['number'][0]) * 100
    else:
        raise UserWarning('Course number is weird in', course)

    # Pull the text contents out of various HTML elements as lists
    course['instructors'] = split_and_flip_instructors(course['instructors'])
    if not course['instructors']:
        del course['instructors']

    if 'gereqs' in course and course['gereqs']:
        course['gereqs'] = parse_links_for_text(course['gereqs'])
        if not course['gereqs']:
            del course['gereqs']

    # process locations and times to create offerings
    locations = course['meetinglocations']
    if locations:
        locations = parse_links_for_text(locations)

    times = course['meetingtimes']
    if times:
        times = parse_paragraph_as_list(times)

    del course['meetinglocations']
    del course['meetingtimes']

    offerings = list(create_offerings(times=times, locations=locations))
    if offerings:
        course['offerings'] = offerings

    # return the non-None values for serialization
    return {key: value for key, value in course.items() if value is not None}


def process_course(course, detail, ignore_revision_keys, dry_run, no_revisions):
    """Combines the 'course' and the 'detail' objects into one. Also 'cleans' the course, to remove html from various
    spots, and cleans up the key names, etc. Also records the revisions to the course."""
    ignore_revision_keys = [] if ignore_revision_keys is None else ignore_revision_keys

    course['title'] = detail.get('title', None)
    course['description'] = detail.get('description', None)

    cleaned = clean_course(course)

    if 'title' in cleaned and cleaned.get('name') == cleaned.get('title'):
        del cleaned['title']

    # course[''] = extract_notes(cleaned)
    cleaned['prerequisites'] = parse_prerequisites(cleaned)

    # I don't remember why I added this check for "did the course already exist", but I needed it for something.
    # TODO: document this
    course_existed_before = check_for_course_file_existence(cleaned['clbid'])
    revisions = check_for_revisions(cleaned, ignore_revision_keys=ignore_revision_keys, no_revisions=no_revisions)
    if course_existed_before and revisions:
        cleaned['revisions'] = revisions

    # There's no reason to save the course if nothing has changed,
    # but we should save if we didn't look for changes.
    # We also must save it if it didn't exist before.
    should_save = not dry_run
    if should_save:
        logging.debug(f"Saving course {cleaned['clbid']}")
        save_course(cleaned)

    return cleaned
