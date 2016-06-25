from collections import OrderedDict
import hashlib
import json
import os

from .paths import info_path
from .log import log


def parse_year_from_filename(filename):
    # ex: 19943.json -> 1994
    return int(filename[0:4])


def json_folder_map(folder, path, dry_run=False):
    output = {
        'files': [],
        'type': 'courses',
    }

    files = os.listdir(folder)
    for filename in files:
        if filename == '.DS_Store':
            continue

        with open(os.path.join(folder, filename), 'rb') as infile:
            info = {
                'path': 'terms/' + filename,
                'hash': hashlib.sha1(infile.read()).hexdigest(),
                'year': parse_year_from_filename(filename)
            }
            output['files'].append(OrderedDict(sorted(info.items())))

    output['files'] = sorted(output['files'], key=lambda item: item['path'])

    output = OrderedDict(sorted(output.items()))

    log('Hashed files')
    if not dry_run:
        with open(info_path, 'w') as outfile:
            outfile.write(json.dumps(output, indent='\t', separators=(',', ': ')))
            outfile.write('\n')
            log('Wrote info.json to', info_path)
