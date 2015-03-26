from .data import departments

def break_apart_departments(course):
	# Split apart the departments, because 'AR/AS' is actually
	# ['ART', 'ASIAN'] departments.
	split = course['deptname'].split('/')
	return [
		departments[dept.lower()] if dept.lower() in departments.keys() else dept for dept in split
	]
