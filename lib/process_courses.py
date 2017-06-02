import json
import re
import html
import logging
import os
from textwrap import dedent

from .break_apart_departments import break_apart_departments
from .check_for_course_revisions import check_for_revisions
from .data import course_types
from .parse_links_for_text import parse_links_for_text
from .parse_paragraph_as_list import parse_paragraph_as_list
from .paths import make_course_path
from .save_data import save_data
from .split_and_flip_instructors import split_and_flip_instructors


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


def extract_notes(course):
    if course['notes'] and 'Will also meet' in course['notes']:
        info = dedent(f'''
            [{course['year']}{course['semester']}] {course['type'][0]} ({'/'.join(course['departments'])} {course['number']} | {course['clbid']} {course['crsid']}):
            \t{course['notes']}
            \t{course['times']} {course['locations']}
        ''')

        # get the timestring and location string out of the notes field
        notes_into_time_and_location_regex = r'.*meet ([MTWF][/-]?.*) in (.*)\.'
        results = re.search(notes_into_time_and_location_regex,
                            course['notes'])
        extra_times, extra_locations = results.groups()
        # print(info + '\n\t' + 'regex matches:', [extra_times, extra_locations])
        print(extra_times)

        # split_time_regex =

        split_location_regex = r'(\w+ ?\d+)(?: or ?(\w+ ?\d+))?'

        # expandedDays = {
        #   'M':  'Mo',
        #   'T':  'Tu',
        #   'W':  'We',
        #   'Th': 'Th',
        #   'F':  'Fr'
        # }

        # listOfDays = []

        # if '-' in daystring:
        #   # M-F, M-Th, T-F
        #   sequence = ['M', 'T', 'W', 'Th', 'F']
        #   startDay = daystring.split('-')[0]
        #   endDay = daystring.split('-')[1]
        #   listOfDays = sequence.slice(
        #       sequence.indexOf(startDay),
        #       sequence.indexOf(endDay) + 1
        #   )
        # else:
        #   # MTThFW
        #   spacedOutDays = daystring.replace(/([a-z]*)([A-Z])/g, '$1 $2')
        #   # The regex sticks an extra space at the front. trim() it.
        #   spacedOutDays = spacedOutDays.trim()
        #   listOfDays = spacedOutDays.split(' ')

        # # 'M' => 'Mo'
        # return list(map(lambda day: expandedDays[day], listOfDays))


def parse_prerequisites(course):
    search_str = 'Prereq'

    in_description = [para[para.index(search_str):]
                      for para in course.get('description', [])
                      if search_str in para]

    if in_description:
        return "\n".join(in_description)

    in_notes = [note[note.index(search_str):]
                for note in course.get('notes', [])
                if search_str in note]

    if in_notes:
        return "\n".join(in_notes)

    return False


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
        print(f"'{course['type']}' doesn't appear in the types list.")
    del course['coursesubtype']

    # Break apart dept names into lists
    course['departments'] = break_apart_departments(course['deptname'])
    del course['deptname']

    # Turn numbers into numbers
    course['clbid'] = int(course['clbid'])

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
    course['crsid'] = int(course['crsid'])
    if course['groupid']:
        course['groupid'] = int(course['groupid'])

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

    # Shorten meetinglocations, meetingtimes, and instructors
    course['locations'] = course['meetinglocations']
    del course['meetinglocations']
    course['times'] = course['meetingtimes']
    del course['meetingtimes']

    # Pull the text contents out of various HTML elements as lists
    course['instructors'] = split_and_flip_instructors(course['instructors'])
    if not course['instructors']:
        del course['instructors']

    if 'gereqs' in course and course['gereqs']:
        course['gereqs'] = parse_links_for_text(course['gereqs'])
        if not course['gereqs']:
            del course['gereqs']
    if 'locations' in course and course['locations']:
        course['locations'] = parse_links_for_text(course['locations'])
        if not course['locations']:
            del course['locations']
    if 'times' in course and course['times']:
        course['times'] = parse_paragraph_as_list(course['times'])
        if not course['times']:
            del course['times']

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
