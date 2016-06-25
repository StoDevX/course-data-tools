"""Load all course files"""
import os
import json
from glob import iglob
from .paths import course_dest


def load_course(path):
    with open(path, 'r', encoding='utf-8') as infile:
        return json.load(infile)


def load_all_courses():
    for file in iglob(os.path.join(course_dest, '*', '*.json')):
        yield load_course(file)
