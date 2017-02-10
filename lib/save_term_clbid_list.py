"""Save the list of clbids for a term into a file"""

import json
from .ensure_dir_exists import ensure_dir_exists
from .paths import make_clbid_map_path, term_clbid_mapping_path


def save_term_clbid_list(term, clbids):
    ensure_dir_exists(term_clbid_mapping_path)
    with open(make_clbid_map_path(term), 'w', encoding='utf-8') as outfile:
        json_data = json.dumps(clbids, indent='\t')
        outfile.write(json_data + '\n')
