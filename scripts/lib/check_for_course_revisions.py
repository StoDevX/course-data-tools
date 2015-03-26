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
		prior_data = load_data_from_file(course_path)
		prior = json.loads(prior_data)
	except FileNotFoundError:
		prior = None

	revisions = []
	# print(course_path, revisions)

	if prior and ('revisions' in prior):
		revisions = prior['revisions']
		del prior['revisions']

	return (prior, revisions or [])


def check_for_revisions(course):
	prior, revisions = load_previous(make_course_path(course['clbid']))

	if not prior:
		return None

	diff = get_old_dict_values(prior, course)
	ordered_diff = OrderedDict()
	for key in sorted(diff.keys()):
		ordered_diff[key] = diff[key]

	if ordered_diff:
		ordered_diff['_updated'] = get_localzone().localize(datetime.now()).isoformat()
		revisions.append(ordered_diff)
		log('revision in %d:' % (course['clbid']), ordered_diff)

	if revisions and (('revisions' not in course) or (revisions != course.get('revisions'))):
		return revisions

	return None
