def regress_course(course):
    if 'departments' in course:
        course['depts'] = course['departments']
        del course['departments']
    if 'description' in course:
        course['desc'] = course['description']
        del course['description']
    if 'number' in course:
        course['num'] = course['number']
        del course['number']
    if 'pn' in course:
        course['pf'] = course['pn']
        del course['pn']
