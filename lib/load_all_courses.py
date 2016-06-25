"""Load all course files"""
import os
import json
from glob import iglob
from .paths import course_dest


def load_all_courses():
    for file in iglob(os.path.join(course_dest, '*', '*.json')):
        with open(file, 'r', encoding='utf-8') as infile:
            course = json.load(infile)
        yield course
