import json
import re
from collections import OrderedDict
import logging

from .break_apart_departments import break_apart_departments
from .check_for_course_revisions import check_for_revisions
from .data import course_types
from .parse_links_for_text import parse_links_for_text
from .parse_paragraph_as_list import parse_paragraph_as_list
from .paths import make_course_path
from .save_data import save_data
from .split_and_flip_instructors import split_and_flip_instructors


def save_course(course):
    course_path = make_course_path(course['clbid'])
    json_course_data = json.dumps(course,
                                  indent='\t',
                                  separators=(',', ': '),
                                  sort_keys=True) + '\n'
    save_data(json_course_data, course_path)


def extract_notes(course):
    if course['notes'] and 'Will also meet' in course['notes']:
        info = '[%d%d] %s (%s %d | %d %d):\n\t%s\n\t%s %s' % (
            course['year'], course['semester'], course['type'][0],
            '/'.join(course['departments']), course['number'],
            course['clbid'], course['crsid'],
            course['notes'],
            course['times'], course['places']
        )

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
    if search_str in course.get('description', ''):
        index = course['description'].index(search_str)
        return course['description'][index:]
    elif search_str in course.get('notes', ''):
        index = course['notes'].index(search_str)
        return course['notes'][index:]
    return False


def clean_course(course):
    # Unescape &amp; in course names
    course['name'] = course['coursename'].replace('&amp;', '&')
    del course['coursename']

    course['section'] = course['coursesection']
    del course['coursesection']

    course['status'] = course['coursestatus']
    del course['coursestatus']

    # Remove <br> tags from the 'notes' field.
    if course['notes']:
        course['notes'] = course['notes'].replace('<br>', ' ')
        course['notes'] = ' '.join(course['notes'].split())

    # Remove the unused varcredits property
    del course['varcredits']

    # Flesh out coursesubtype
    if course['coursesubtype'] and course['coursesubtype'] in course_types:
        course['type'] = course_types[course['coursesubtype']]
    else:
        course['type'] = course['coursesubtype']
        print(course['type'], 'doesn\'t appear in the types list.')
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


def process_course(course, detail, find_revisions, ignore_revisions, dry_run):
    ignore_revisions = [] if ignore_revisions is None else ignore_revisions

    course['title'] = detail.get('title', None)
    course['description'] = detail.get('description', None)

    cleaned = clean_course(course)

    if 'title' in cleaned and cleaned.get('name') == cleaned.get('title'):
        del cleaned['title']

    # course[''] = extract_notes(cleaned)
    cleaned['prerequisites'] = parse_prerequisites(cleaned)

    if find_revisions:
        revisions = check_for_revisions(cleaned, ignore_revisions=ignore_revisions)
        if revisions:
            cleaned['revisions'] = revisions
    else:
        revisions = []

    # There's no reason to save the course if nothing has changed
    # But we should save if we didn't look for changes
    if (revisions or not find_revisions) and (not dry_run):
        logging.debug('Saving course')
        save_course(cleaned)

    return cleaned
