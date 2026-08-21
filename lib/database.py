"""Write course data into a normalized SQLite catalog.

The JSON course files are the source of truth; this database is a derived view
rebuilt from scratch on every run. Sections are keyed on their clbid so that a
rebuild updates rows in place rather than accumulating duplicates.
"""

# Instructors and gereqs are shared across sections, so each lives in its own
# lookup table joined many-to-many. Everything here maps a lookup table to the
# column holding its value and the join table pointing back at a section.
LOOKUPS = {
    'instructors': ('instructor', 'name', 'section_instructor', 'instructor_id'),
    'gereqs': ('gereq', 'code', 'section_gereq', 'gereq_id'),
}


def create_schema(db):
    """Create the catalog tables and their indexes if they do not yet exist."""
    db["section"].create({
        "clbid": int,
        "crsid": int,
        "term": int,
        "year": int,
        "semester": int,
        "department": str,
        "number": str,
        "section": str,
        "level": int,
        "type": str,
        "name": str,
        "title": str,
        "description": str,
        "credits": float,
        "pass_nopass": int,
        "learning_mode": str,
        "status": str,
        "enrolled": int,
        "enrollment_max": int,
        "enrollment_fy": str,
        "enrollment_so": str,
        "enrollment_jr": str,
        "enrollment_sr": str,
        "notes": str,
    }, pk="clbid", if_not_exists=True)
    db["section"].create_index(["term"], if_not_exists=True)
    db["section"].create_index(["department"], if_not_exists=True)

    db["instructor"].create({
        "id": int,
        "name": str,
    }, pk="id", if_not_exists=True)
    db["instructor"].create_index(["name"], unique=True, if_not_exists=True)

    db["gereq"].create({
        "id": int,
        "code": str,
    }, pk="id", if_not_exists=True)
    db["gereq"].create_index(["code"], unique=True, if_not_exists=True)

    db["offering"].create({
        "id": int,
        "clbid": int,
        "day": str,
        "start": str,
        "end": str,
        "location": str,
    }, pk="id", foreign_keys=[("clbid", "section", "clbid")], if_not_exists=True)
    db["offering"].create_index(["clbid"], if_not_exists=True)

    db["section_instructor"].create({
        "clbid": int,
        "instructor_id": int,
    }, pk=("clbid", "instructor_id"), foreign_keys=[
        ("clbid", "section", "clbid"),
        ("instructor_id", "instructor", "id"),
    ], if_not_exists=True)

    db["section_gereq"].create({
        "clbid": int,
        "gereq_id": int,
    }, pk=("clbid", "gereq_id"), foreign_keys=[
        ("clbid", "section", "clbid"),
        ("gereq_id", "gereq", "id"),
    ], if_not_exists=True)


def join_paragraphs(value):
    """Descriptions and notes are lists of strings in the course JSON."""
    return "\n".join(value) if value else ""


def build_section(course):
    return {
        "clbid": int(course["clbid"]),
        "crsid": int(course["crsid"]),
        "term": int(course["term"]),
        "year": int(course["year"]),
        "semester": int(course["semester"]),
        "department": course.get("department"),
        "number": str(course["number"]) if "number" in course else None,
        "section": course.get("section"),
        "level": course.get("level"),
        "type": course.get("type"),
        "name": course.get("name"),
        "title": course.get("title"),
        "description": join_paragraphs(course.get("description")),
        "credits": course.get("credits"),
        "pass_nopass": 1 if course.get("pn") else 0,
        "learning_mode": course.get("learningmode") or "",
        "status": course.get("status"),
        "enrolled": course.get("enrolled"),
        "enrollment_max": course.get("max"),
        "enrollment_fy": course.get("firstyear"),
        "enrollment_so": course.get("sophomore"),
        "enrollment_jr": course.get("junior"),
        "enrollment_sr": course.get("senior"),
        "notes": join_paragraphs(course.get("notes")),
    }


def build_offering(clbid, offering):
    return {
        "clbid": clbid,
        "day": offering["day"],
        "start": offering["start"],
        "end": offering["end"],
        "location": offering["location"],
    }


def link_lookups(db, clbid, course):
    """Point this section at its shared instructor and gereq rows."""
    for key, (table, column, join_table, join_column) in LOOKUPS.items():
        db[join_table].delete_where("clbid = ?", [clbid])
        for value in course.get(key) or []:
            row_id = db[table].lookup({column: value})
            db[join_table].insert(
                {"clbid": clbid, join_column: row_id},
                replace=True,
            )


def insert_course(db, course):
    clbid = int(course["clbid"])

    db["section"].insert(build_section(course), pk="clbid", replace=True)

    # A rebuild must replace a section's child rows, never append to them.
    db["offering"].delete_where("clbid = ?", [clbid])
    offerings = [build_offering(clbid, o) for o in course.get("offerings") or []]
    if offerings:
        db["offering"].insert_all(offerings)

    link_lookups(db, clbid, course)


def tracer(sql, params):
    print(f'SQL: {sql} - params: {params}')
