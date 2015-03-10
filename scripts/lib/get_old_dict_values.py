from .KEYNOTFOUND import KEYNOTFOUNDIN1
from .dict_diff import dict_diff

def get_old_dict_values(old, new):
	# Returns the "old" value for two dicts.
	diff = dict_diff(old, new)

	return {key: diff[key][0]
		if diff[key][0] != KEYNOTFOUNDIN1
		else None
		for key in diff}
