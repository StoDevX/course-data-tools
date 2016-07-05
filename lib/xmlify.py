import xmltodict
from collections import OrderedDict


def xmlify(data):
    data = [OrderedDict(sorted(d.items())) for d in data]
    massaged = {'root': {'course': data}}
    return xmltodict.unparse(massaged, pretty=True)
