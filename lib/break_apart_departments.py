from .data import departments


def break_apart_departments(depts):
    # Split apart the departments, because 'AR/AS' is actually
    # ['ART', 'ASIAN'] departments.
    return [
        departments[dept.lower()] if dept.lower() in departments.keys() else dept
        for dept in depts.split('/')
    ]
