from bs4 import BeautifulSoup


def parse_paragraph_as_list(string_with_br):
    strings = BeautifulSoup(string_with_br, 'html.parser').strings
    splitted = [' '.join(s.split()).strip() for s in strings]
    return [s for s in splitted if s]
