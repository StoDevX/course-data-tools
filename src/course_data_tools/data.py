from os.path import join
import json
from .paths import handmade_path

with open(join(handmade_path, "course_types.json")) as types:
    course_types = json.loads(types.read())
