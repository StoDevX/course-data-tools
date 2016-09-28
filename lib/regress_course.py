def regress_course(course):
    course['depts'] = course['departments']
    del course['departments']
    course['desc'] = course['description']
    del course['description']
    course['num'] = course['number']
    del course['number']
    course['pf'] = course['pn']
    del course['pn']
