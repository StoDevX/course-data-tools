"""Process course data from the CFC API.

The API returns cleaner data than the XML feed, so this is simpler than
process_courses.py. We still merge in description/title from fetch_course_details
and handle revisions.
"""
import json
import logging
import os

from .check_for_course_revisions import check_for_revisions
from .paths import make_course_path
from .save_data import save_data
from .parse_prerequisites import parse_prerequisites
from . import data


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


def process_course_from_api(course, detail, ignore_revision_keys, dry_run, no_revisions):
    """Process a course from the API and merge in details.

    The API data is already mostly clean, so we just need to:
    1. Merge title/description from detail
    2. Map type code to name
    3. Parse prerequisites
    4. Handle revisions
    5. Save to disk
    """
    ignore_revision_keys = [] if ignore_revision_keys is None else ignore_revision_keys

    # Merge title/description from detail fetch
    course['title'] = detail.get('title')
    course['description'] = detail.get('description')

    # Map type code to human name
    types = data.course_types()
    if course.get('type') and course['type'] in types:
        course['type'] = types[course['type']]

    # Remove title if it duplicates name
    if course.get('title') and course.get('name') == course.get('title'):
        del course['title']

    # Parse prerequisites from description (needs description to exist)
    if course.get('description'):
        course['prerequisites'] = parse_prerequisites(course)

    # Handle revisions
    course_existed_before = check_for_course_file_existence(course['clbid'])
    revisions = check_for_revisions(course, ignore_revision_keys=ignore_revision_keys, no_revisions=no_revisions)
    if course_existed_before and revisions:
        course['revisions'] = revisions

    # Filter out None values
    course = {k: v for k, v in course.items() if v is not None}

    # Save
    if not dry_run:
        logging.debug(f"Saving course {course['clbid']}")
        save_course(course)

    return course
