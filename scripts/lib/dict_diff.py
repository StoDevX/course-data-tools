from .KEYNOTFOUND import KEYNOTFOUNDIN1, KEYNOTFOUNDIN2

def dict_diff(first, second):
	# from http://code.activestate.com/recipes/576644-diff-two-dictionaries/#c6
	"""
	Return a dict of keys that differ with another config object.  If a value is
	not found in one fo the configs, it will be represented by KEYNOTFOUND.
	@param first:   Fist dictionary to diff.
	@param second:  Second dicationary to diff.
	@return diff:   Dict of Key => (first.val, second.val)
	"""

	diff = {}
	sd1 = set(first)
	sd2 = set(second)
	# Keys missing in the second dict
	for key in sd1.difference(sd2):
		diff[key] = (first[key], KEYNOTFOUNDIN2)
	# Keys missing in the first dict
	for key in sd2.difference(sd1):
		diff[key] = (KEYNOTFOUNDIN1, second[key])
	# Check for differences
	for key in sd1.intersection(sd2):
		if first[key] != second[key]:
			diff[key] = (first[key], second[key])
	return diff
