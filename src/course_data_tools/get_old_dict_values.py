KEYNOTFOUNDIN1 = '<KEY NOT FOUND IN 1>'  # KeyNotFound for dictDiff
KEYNOTFOUNDIN2 = '<KEY NOT FOUND IN 2>'  # KeyNotFound for dictDiff


def dict_diff(first, second):
    # from http://code.activestate.com/recipes/576644-diff-two-dictionaries/#c6
    """
    Return a dict of keys that differ with another config object.  If a value
    is not found in one of the configs, it will be represented by KEYNOTFOUND.
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


def get_old_dict_values(old, new):
    # Returns the "old" value for two dicts.
    diff = dict_diff(old, new)

    return {key: diff[key][0]
            if diff[key][0] != KEYNOTFOUNDIN1
            else None
            for key in diff}
