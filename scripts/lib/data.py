import json
from .paths import handmade_path

departments = None
with open(handmade_path + 'to_department_abbreviations.json') as depts:
    departments = json.loads(depts.read())

course_types = None
with open(handmade_path + 'course_types.json') as types:
    course_types = json.loads(types.read())
