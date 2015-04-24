from .load_data_from_file import load_data_from_file
from .save_data import save_data
from .paths import mappings_path
import json


def maintain_lists_of_entries(all_courses, dry_run=False):
    entry_list_path = mappings_path

    data_sets = {
        'departments': [],
        'professors': [],
        'times': [],
        'locations': [],
        'gereqs': [],
        'types': [],
    }

    for set_name, set_data in data_sets.items():
        filename = entry_list_path + 'valid_' + set_name + '.json'
        data = load_data_from_file(filename)
        data_sets[set_name] = json.loads(data)[set_name]

    for course in all_courses:
        data_sets['departments'].extend(course.get('depts') or [])
        data_sets['professors'].extend(course.get('profs') or [])
        data_sets['times'].extend(course.get('times') or [])
        data_sets['locations'].extend(course.get('places') or [])
        data_sets['gereqs'].extend(course.get('gereqs') or [])
        data_sets['types'].append(course.get('type') or [])

    data_sets['departments'] = sorted(set(data_sets['departments']))
    data_sets['professors'] = sorted(set(data_sets['professors']))
    data_sets['times'] = sorted(set(data_sets['times']))
    data_sets['locations'] = sorted(set(data_sets['locations']))
    data_sets['gereqs'] = sorted(set(data_sets['gereqs']))
    data_sets['types'] = sorted(set(data_sets['types']))

    for set_name, set_data in data_sets.items():
        filename = entry_list_path + 'valid_' + set_name + '.json'
        json_data = json.dumps({set_name: set_data}, indent='\t', separators=(',', ': '))
        if not dry_run:
            save_data(json_data, filename)
