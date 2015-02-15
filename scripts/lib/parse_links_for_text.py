from bs4 import BeautifulSoup

def parse_links_for_text(string_with_links):
	return [link.get_text() for link in BeautifulSoup(string_with_links).find_all('a')]
