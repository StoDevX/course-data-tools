import re
LINK_REGEX = re.compile(r'<a.*?>(.*?)<\/a>')


def parse_links_for_text(string_with_links):
    strings = [link.group(1)
               for link in LINK_REGEX.finditer(string_with_links)
               if link]

    split_strings = [' '.join(s.split()).strip() for s in strings]
    return [s for s in split_strings if s]
