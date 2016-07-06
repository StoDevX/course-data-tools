from bs4 import BeautifulSoup


def parse_links_for_text(string_with_links):
    strings = [link.get_text()
               for link in BeautifulSoup(string_with_links, 'html.parser').find_all('a')]
    splitted = [' '.join(s.split()).strip() for s in strings]
    return [s for s in splitted if s]
