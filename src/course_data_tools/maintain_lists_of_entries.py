from .load_data_from_file import load_data_from_file
from .save_data import save_data
from .paths import mappings_path
import json
import os


def maintain_lists_of_entries(all_courses):
    data_sets = {
        "departments": set(),
        "instructors": set(),
        "times": set(),
        "locations": set(),
        "gereqs": set(),
        "types": set(),
    }

    for key in data_sets:
        filename = os.path.join(mappings_path, f"valid_{key}.json")
        data = load_data_from_file(filename)
        data_sets[key] = set(json.loads(data))

    for course in all_courses:
        data_sets["departments"].update(course.get("departments", []))
        data_sets["instructors"].update(course.get("instructors", []))
        data_sets["times"].update(course.get("times", []))
        data_sets["locations"].update(course.get("places", []))
        data_sets["gereqs"].update(course.get("gereqs", []))
        data_sets["types"].add(course.get("type", ""))

    for key in data_sets:
        data_sets[key] = sorted(data_sets[key])

    for key, data in data_sets.items():
        filename = os.path.join(mappings_path, f"valid_{key}.json")
        json_data = json.dumps(data, indent="\t", ensure_ascii=False)
        save_data(json_data + "\n", filename)
