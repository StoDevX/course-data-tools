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

# Text fields interned into their own lookup tables for compression.
# Maps JSON key -> (table_name, section_fk_column, is_list).
# is_list=True means the JSON value is a list of strings to join.
INTERNED_TEXT = {
    'description': ('description_text', 'description_id', True),
    'name': ('name_text', 'name_id', False),
    'title': ('title_text', 'title_id', False),
    'notes': ('notes_text', 'notes_id', True),
}


def create_schema(db):
    """Create the catalog tables and their indexes if they do not yet exist."""
    # Interned text lookup tables — created first so section can reference them.
    for table, fk_col, _ in INTERNED_TEXT.values():
        db[table].create({"id": int, "text": str}, pk="id", if_not_exists=True)
        db[table].create_index(["text"], unique=True, if_not_exists=True)

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
        "name_id": int,
        "title_id": int,
        "description_id": int,
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
        "notes_id": int,
    }, pk="clbid", foreign_keys=[
        (fk_col, table, "id") for table, fk_col, _ in INTERNED_TEXT.values()
    ], if_not_exists=True)
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

    db["location"].create({
        "id": int,
        "name": str,
    }, pk="id", if_not_exists=True)
    db["location"].create_index(["name"], unique=True, if_not_exists=True)

    db["timeslot"].create({
        "id": int,
        "day": str,
        "start": str,
        "end": str,
    }, pk="id", if_not_exists=True)
    db["timeslot"].create_index(["day", "start", "end"], unique=True, if_not_exists=True)

    db["offering"].create({
        "id": int,
        "clbid": int,
        "timeslot_id": int,
        "location_id": int,
    }, pk="id", foreign_keys=[
        ("clbid", "section", "clbid"),
        ("timeslot_id", "timeslot", "id"),
        ("location_id", "location", "id"),
    ], if_not_exists=True)
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

    # Compatibility VIEWs that join interned text back for existing queries.
    db.execute("""
        CREATE VIEW IF NOT EXISTS section_full AS
        SELECT
            s.clbid, s.crsid, s.term, s.year, s.semester,
            s.department, s.number, s.section, s.level, s.type,
            n.text AS name,
            t.text AS title,
            d.text AS description,
            s.credits, s.pass_nopass, s.learning_mode, s.status,
            s.enrolled, s.enrollment_max,
            s.enrollment_fy, s.enrollment_so, s.enrollment_jr, s.enrollment_sr,
            nt.text AS notes
        FROM section s
        LEFT JOIN name_text n ON s.name_id = n.id
        LEFT JOIN title_text t ON s.title_id = t.id
        LEFT JOIN description_text d ON s.description_id = d.id
        LEFT JOIN notes_text nt ON s.notes_id = nt.id
    """)

    db.execute("""
        CREATE VIEW IF NOT EXISTS offering_full AS
        SELECT
            o.id, o.clbid,
            ts.day, ts.start, ts.end,
            loc.name AS location
        FROM offering o
        LEFT JOIN timeslot ts ON o.timeslot_id = ts.id
        LEFT JOIN location loc ON o.location_id = loc.id
    """)


def join_paragraphs(value):
    """Descriptions and notes are lists of strings in the course JSON."""
    return "\n".join(value) if value else ""


def intern_text(db, table, text):
    """Return the id of a row in `table` containing `text`, inserting if needed.

    Returns None if text is empty or None.
    """
    if not text:
        return None
    return db[table].lookup({"text": text})


def build_section(db, course):
    row = {
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
    }
    for json_key, (table, fk_col, is_list) in INTERNED_TEXT.items():
        value = course.get(json_key)
        text = join_paragraphs(value) if is_list else value
        row[fk_col] = intern_text(db, table, text)
    return row


def build_offering(db, clbid, offering):
    timeslot_id = db["timeslot"].lookup({
        "day": offering["day"],
        "start": offering["start"],
        "end": offering["end"],
    })
    location_id = db["location"].lookup({"name": offering["location"]})
    return {
        "clbid": clbid,
        "timeslot_id": timeslot_id,
        "location_id": location_id,
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

    db["section"].insert(build_section(db, course), pk="clbid", replace=True)

    # A rebuild must replace a section's child rows, never append to them.
    db["offering"].delete_where("clbid = ?", [clbid])
    offerings = [build_offering(db, clbid, o) for o in course.get("offerings") or []]
    if offerings:
        db["offering"].insert_all(offerings)

    link_lookups(db, clbid, course)


def tracer(sql, params):
    print(f'SQL: {sql} - params: {params}')
