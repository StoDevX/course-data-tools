import re
linkre = re.compile(r'<a.*?>(.*?)<\/a>')


def parse_links_for_text(string_with_links):
    matches = linkre.finditer(string_with_links)
    strings = [link.group(1) for link in matches if link]
    splitted = [' '.join(s.split()).strip() for s in strings]
    return [s for s in splitted if s]
