import csv
import io


def get_all_keys(list_of_objects):
    return sorted(set([key for obj in list_of_objects for key in obj.keys()]))


def csvify(data):
    for item in data:
        if 'revisions' in item:
            item.pop('revisions')
        for key in item:
            if type(item[key]) is str:
                item[key] = item[key].replace('\n', '\\n')
    with io.StringIO() as outfile:
        csv_file = csv.DictWriter(outfile, get_all_keys(data))
        csv_file.writeheader()
        csv_file.writerows(data)
        str_contents = outfile.getvalue()
    return str_contents
