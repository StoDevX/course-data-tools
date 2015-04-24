import re


def fix_invalid_xml(raw):
    # Replace any invalid XML entities with &amp;
    regex = re.compile(r'&(?!(?:[a-z]+|#[0-9]+|#x[0-9a-f]+);)')
    subst = '&amp;'
    cleaned = re.sub(regex, subst, raw)
    return cleaned
