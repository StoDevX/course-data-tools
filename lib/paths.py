from os.path import join

COURSE_DATA = join('..', 'course-data')
details_source = join(COURSE_DATA, 'details')
xml_source = join(COURSE_DATA, 'raw_xml')
course_dest = join(COURSE_DATA, 'courses')
info_path = join(COURSE_DATA, 'info.json')
term_dest = join(COURSE_DATA, 'terms')
mappings_path = join(COURSE_DATA, 'data-lists')
handmade_path = join(COURSE_DATA, 'data-mappings')
term_clbid_mapping_path = join(COURSE_DATA, 'courses', '_index')


def make_clbid_map_path(term):
    return join(term_clbid_mapping_path, str(term) + '.json')


def find_details_subdir(clbid):
    str_clbid = str(clbid).zfill(10)

    n_thousand = int(int(clbid) / 1000)
    thousands_subdir = (n_thousand * 1000)

    return join(str(thousands_subdir).zfill(5), str_clbid)


def make_course_path(clbid):
    clbid = str(clbid).zfill(10)
    return join(course_dest, find_details_subdir(clbid) + '.json')


def make_html_path(clbid):
    clbid = str(clbid).zfill(10)
    return join(details_source, find_details_subdir(clbid) + '.html')


def make_xml_term_path(term):
    return join(xml_source, str(term) + '.xml')


def make_built_term_path(term, kind, folder=term_dest):
    return join(folder, str(term) + '.' + kind)
