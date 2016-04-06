from collections import OrderedDict
from tzlocal import get_localzone
from datetime import datetime
from datadiff import diff as pretty_diff
import json

from .load_data_from_file import load_data_from_file
from .get_old_dict_values import get_old_dict_values
from .log import log
from .paths import make_course_path


def load_previous(course_path):
    try:
        prior_data = load_data_from_file(course_path)
    except FileNotFoundError:
        prior_data = None

    try:
        prior = json.loads(prior_data)
    except Exception:
        print("Error loading JSON")
        print(prior_data)
        prior = None

    revisions = []
    # print(course_path, revisions)

    if prior and ('revisions' in prior):
        revisions = prior['revisions']
        del prior['revisions']

    return (prior, revisions or [])


def check_for_revisions(course, ignore_revisions):
    prior, revisions = load_previous(make_course_path(course['clbid']))

    if not prior:
        return None

    diff = get_old_dict_values(prior, course)
    ordered_diff = OrderedDict()
    for key in sorted(diff.keys()):
        if key not in ignore_revisions:
            ordered_diff[key] = diff[key]

    if ordered_diff:
        now = get_localzone().localize(datetime.now())
        ordered_diff['_updated'] = now.isoformat()
        revisions.append(ordered_diff)
        log('revision:', pretty_diff(a=prior, b=course, fromfile='old', tofile='new'))

    if revisions and ('revisions' not in course or revisions != course.get('revisions')):
        return revisions

    return None
