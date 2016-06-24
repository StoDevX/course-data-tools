details_source = './course-data/details/'
xml_source = './course-data/raw_xml/'
course_dest = './course-data/courses/'
info_path = './build/info.json'
term_dest = './build/terms/'
mappings_path = './course-data/data/generated/'
handmade_path = './course-data/data/handmade/'


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


def make_built_term_path(term, kind, dir=term_dest):
    return dir + str(term) + '.' + kind
