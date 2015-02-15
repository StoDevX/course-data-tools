from .find_details_subdir import find_details_subdir

details_source = './source/details/'
xml_source     = './source/raw_xml/'
term_dest      = './courses/terms/'
course_dest    = './source/courses/'
info_path      = './courses/info.json'
mappings_path  = './related-data/generated/'
handmade_path  = './related-data/handmade/'

def make_course_path(clbid):
	clbid = str(clbid).zfill(10)
	course_path = course_dest + find_details_subdir(clbid) + '.json'
	return course_path
