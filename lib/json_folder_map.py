from collections import OrderedDict
import hashlib
import json
import os

from .paths import info_path
from .log import log


def json_folder_map(folder, path, dry_run=False):
    output = {
        'files': [],
        'type': 'courses',
    }

    files = os.scandir(folder)
    for file in files:
        filename = file.name
        if filename.startswith('.'):
            continue

        filepath = os.path.join(folder, filename)
        with open(filepath, 'rb') as infile:
            basename, extension = os.path.splitext(filename)
            extension = extension[1:]  # splitext's extension includes the preceding dot

            info = {
                'path': 'terms/' + filename,
                'hash': hashlib.sha256(infile.read()).hexdigest(),
                'year': int(basename[0:4]),  # eg: 19943.json -> 1994
                'term': int(basename),  # eg: 19943.json -> 19943
                'type': extension,
            }

            output['files'].append(OrderedDict(sorted(info.items())))

    output['files'] = sorted(output['files'], key=lambda item: item['path'])
    output = OrderedDict(sorted(output.items()))

    log('Hashed files')
    if not dry_run:
        with open(info_path, 'w') as outfile:
            outfile.write(json.dumps(output, indent='\t', separators=(',', ': ')))
            outfile.write('\n')
            log('Wrote index.json to', info_path)
