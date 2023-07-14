from collections import OrderedDict
from datetime import datetime, timezone
import json

from structlog.stdlib import get_logger

from .get_old_dict_values import get_old_dict_values
from .paths import make_course_path

logger = get_logger()


def load_previous(course_path):
    try:
        with open(course_path, "r", encoding="utf-8") as infile:
            return json.load(infile)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        logger.error("Error decoding old jsonified course %s", course_path)


def sort_diff(diff, ignore_revision_keys):
    ordered_diff = OrderedDict()
    for key in sorted(diff.keys()):
        if key not in ignore_revision_keys:
            ordered_diff[key] = diff[key]
    return ordered_diff


def check_for_revisions(course, ignore_revision_keys, no_revisions):
    prior = load_previous(make_course_path(course["clbid"]))

    if not prior:
        return None

    if no_revisions:
        return prior.get("revisions", None)

    if "revisions" in prior:
        revisions = prior["revisions"]
        del prior["revisions"]
    else:
        revisions = []

    diff = get_old_dict_values(prior, course)
    if not diff:
        return revisions

    ordered_diff = sort_diff(diff, ignore_revision_keys=ignore_revision_keys)

    if ordered_diff:
        ordered_diff["_updated"] = datetime.now(timezone.utc)
        revisions.append(ordered_diff)

    return revisions
