import json
from .paths import handmade_path

with open(handmade_path + 'to_department_abbreviations.json') as depts:
    departments = json.loads(depts.read())

with open(handmade_path + 'course_types.json') as types:
    course_types = json.loads(types.read())
