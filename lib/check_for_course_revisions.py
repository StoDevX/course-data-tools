from collections import OrderedDict
from tzlocal import get_localzone
from datetime import datetime
import json

from .load_data_from_file import load_data_from_file
from .get_old_dict_values import get_old_dict_values
from .log import log
from .paths import make_course_path


def load_previous(course_path):
    try:
        with open(course_path, 'r', encoding='utf-8') as infile:
            return json.load(infile)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        log("Error decoding old jsonified course %s", course_path)


def sort_diff(diff, ignore_revisions):
    ordered_diff = OrderedDict()
    for key in sorted(diff.keys()):
        if key not in ignore_revisions:
            ordered_diff[key] = diff[key]
    return ordered_diff


def check_for_revisions(course, ignore_revisions):
    prior = load_previous(make_course_path(course['clbid']))

    if not prior:
        return None

    if 'revisions' in prior:
        revisions = prior['revisions']
        del prior['revisions']
    else:
        return None

    if prior == course:
        return course.get('revisions', None)

    diff = get_old_dict_values(prior, course)
    if not diff:
        return None

    ordered_diff = sort_diff(diff, ignore_revisions=ignore_revisions)

    # TODO: Change these to run in UTC, rather than local time.
    # Also it's slow. Very slow.
    # Of the 0.894361s this function takes total on 20151,
    # the next line accounts for 0.055712s of that.
    # For only two calls.
    now = get_localzone().localize(datetime.now())
    ordered_diff['_updated'] = now.isoformat()
    revisions.append(ordered_diff)

    return revisions
