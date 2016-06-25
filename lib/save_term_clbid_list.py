"""Save the list of clbids for a term into a file"""

import json
from .paths import make_clbid_map_path, term_clbid_mapping_path


def save_term_clbid_list(term, clbids):
    with open(make_clbid_map_path(term), 'w', encoding='utf-8') as outfile:
        json_data = json.dumps(clbids, outfile, indent='\t', separators=(',', ': '))
        outfile.write(json_data + '\n')
