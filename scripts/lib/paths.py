details_source = './source/details/'
xml_source     = './source/raw_xml/'
course_dest    = './source/courses/'
info_path      = './courses/info.json'
term_dest      = './courses/terms/'
mappings_path  = './related-data/generated/'
handmade_path  = './related-data/handmade/'


def find_details_subdir(clbid):
	str_clbid = str(clbid).zfill(10)

	n_thousand = int(int(clbid) / 1000)
	thousands_subdir = (n_thousand * 1000)

	return str(thousands_subdir).zfill(5) + '/' + str_clbid


def make_course_path(clbid):
	clbid = str(clbid).zfill(10)
	return course_dest + find_details_subdir(clbid) + '.json'

def make_html_path(clbid):
	clbid = str(clbid).zfill(10)
	return details_source + find_details_subdir(clbid) + '.html'

def make_xml_term_path(term):
	return xml_source + str(term) + '.xml'

def make_json_term_path(term):
	return term_dest + str(term) + '.json'
