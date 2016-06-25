"""Load all course files"""
import os
import json
from .paths import course_dest, make_course_path, make_clbid_map_path


def load_course(path):
    with open(path, 'r', encoding='utf-8') as infile:
        return json.load(infile)


def load_all_courses():
    for folder in os.scandir(course_dest):
        if not folder.is_dir() or folder.name.startswith('_'):
            continue
        for file in os.scandir(folder.path):
            yield load_course(file.path)


def load_course_by_clbid(clbid):
    return load_course(make_course_path(clbid))


def load_some_courses(term):
    with open(make_clbid_map_path(term), 'r', encoding='utf-8') as infile:
        clbids = json.load(infile)
    return [load_course_by_clbid(clbid) for clbid in clbids]
