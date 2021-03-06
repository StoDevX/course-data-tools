from os.path import join

COURSE_DATA = join('..', 'course-data')
details_source = join(COURSE_DATA, 'details')
xml_source = join(COURSE_DATA, 'raw_xml')
course_dest = join(COURSE_DATA, 'courses')
term_dest = join(COURSE_DATA)
mappings_path = join(COURSE_DATA, 'data-lists')
handmade_path = join(COURSE_DATA, 'data-mappings')
term_clbid_mapping_path = join(COURSE_DATA, 'courses', '_index')


def make_clbid_map_path(term):
    return join(term_clbid_mapping_path, str(term) + '.json')


def find_details_subdir(clbid):
    str_clbid = str(clbid).zfill(10)

    n_thousand = int(clbid) // 1000
    thousands_subdir = str(n_thousand * 1000).zfill(5)

    return join(thousands_subdir, str_clbid)


def make_course_path(clbid):
    return join(course_dest, f'{find_details_subdir(clbid)}.json')


def make_detail_path(clbid):
    return join(details_source, f'{find_details_subdir(clbid)}.json')


def make_xml_term_path(term):
    return join(xml_source, f'{term}.xml')


def make_built_term_path(term, kind):
    return f'{term}.{kind}'
