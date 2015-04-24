from bs4 import BeautifulSoup


def parse_paragraph_as_list(string_with_br):
    return list(BeautifulSoup(string_with_br).strings)
