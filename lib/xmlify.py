import xmltodict
from collections import OrderedDict


def xmlify(data):
    for course in data:
        if 'revisions' in course:
            course['revisions'] = [OrderedDict(sorted(rev.items()))
                                   for rev in course['revisions']]
    data = [OrderedDict(sorted(c.items())) for c in data]
    massaged = {'root': {'course': data}}
    return xmltodict.unparse(massaged, pretty=True)
