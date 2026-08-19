from os.path import join
import json
from .paths import handmade_path

_cache = None


def course_types():
    """The SIS coursesubtype code mapping, owned by the course-data repo.

    Read on first use rather than at import, so that importing these modules
    does not require the data repository to be checked out.
    """
    global _cache
    if _cache is None:
        with open(join(handmade_path, 'course_types.json')) as types:
            _cache = json.loads(types.read())
    return _cache
