from functools import cache
from os.path import join
import json
from .paths import handmade_path


@cache
def course_types():
    """The SIS coursesubtype code mapping, owned by the course-data repo.

    Read on first use rather than at import, so that importing these modules
    does not require the data repository to be checked out.
    """
    with open(join(handmade_path, 'course_types.json')) as types:
        return json.loads(types.read())
