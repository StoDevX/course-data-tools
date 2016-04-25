import re

REGEX = re.compile(r'&(?!(?:[a-z]+|#[0-9]+|#x[0-9a-f]+);)')


def fix_invalid_xml(raw):
    # Replace any invalid XML entities with &amp;
    subst = '&amp;'
    cleaned = re.sub(REGEX, subst, raw)
    return cleaned
