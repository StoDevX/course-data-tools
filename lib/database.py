"""Write course data into a normalized SQLite catalog.

The JSON course files are the source of truth; this database is a derived view
rebuilt from scratch on every run. Sections are keyed on their clbid so that a
rebuild updates rows in place rather than accumulating duplicates.
"""

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
        "enrolled_fy": int,
        "enrolled_so": int,
        "enrolled_jr": int,
        "enrolled_sr": int,
        "max_fy": int,
        "max_so": int,
        "max_jr": int,
        "max_sr": int,
        "notes_id": int,
    }, pk="clbid", foreign_keys=[
        (fk_col, table, "id") for table, fk_col, _ in INTERNED_TEXT.values()
    ], if_not_exists=True)
    db["section"].create_index(["term"], if_not_exists=True)
    db["section"].create_index(["department"], if_not_exists=True)

    db["instructor"].create({
        "id": int,
        "fsnum": str,
        "name": str,
    }, pk="id", if_not_exists=True)
    db["instructor"].create_index(["fsnum"], unique=True, if_not_exists=True)
    db["instructor"].create_index(["name"], if_not_exists=True)  # not unique - names can change

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
            s.enrolled_fy, s.enrolled_so, s.enrolled_jr, s.enrolled_sr,
            s.max_fy, s.max_so, s.max_jr, s.max_sr,
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


def _parse_class_year_enrollment(course, old_key, new_enrolled_key, new_max_key):
    """Extract enrolled/max from either old "0/0" format or new integer columns."""
    # New API format: separate integer columns
    if new_enrolled_key in course:
        return course.get(new_enrolled_key), course.get(new_max_key)
    # Old format: "enrolled/max" string
    value = course.get(old_key)
    if value and "/" in str(value):
        parts = str(value).split("/")
        enrolled = int(parts[0]) if parts[0].isdigit() else None
        max_val = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        return enrolled, max_val
    return None, None


def build_section(db, course):
    fy_enrolled, fy_max = _parse_class_year_enrollment(
        course, "firstyear", "enrollment_fy", "max_fy")
    so_enrolled, so_max = _parse_class_year_enrollment(
        course, "sophomore", "enrollment_so", "max_so")
    jr_enrolled, jr_max = _parse_class_year_enrollment(
        course, "junior", "enrollment_jr", "max_jr")
    sr_enrolled, sr_max = _parse_class_year_enrollment(
        course, "senior", "enrollment_sr", "max_sr")

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
        "enrolled_fy": fy_enrolled,
        "enrolled_so": so_enrolled,
        "enrolled_jr": jr_enrolled,
        "enrolled_sr": sr_enrolled,
        "max_fy": fy_max,
        "max_so": so_max,
        "max_jr": jr_max,
        "max_sr": sr_max,
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


def _link_instructors(db, clbid, course):
    """Link section to instructor rows, using FSNUM when available."""
    db["section_instructor"].delete_where("clbid = ?", [clbid])

    instructors_full = course.get("instructors_full") or []
    instructors = course.get("instructors") or []

    # Build a map from name to fsnum for fast lookup
    fsnum_by_name = {i["name"]: i.get("fsnum") for i in instructors_full}

    for name in instructors:
        fsnum = fsnum_by_name.get(name)

        if fsnum:
            # FSNUM-based lookup: update name if it changed
            existing = list(db["instructor"].rows_where("fsnum = ?", [fsnum]))
            if existing:
                row_id = existing[0]["id"]
                if existing[0]["name"] != name:
                    db["instructor"].update(row_id, {"name": name})
            else:
                row_id = db["instructor"].insert({"fsnum": fsnum, "name": name}).last_pk
        else:
            # No FSNUM: fall back to name-based lookup
            existing = list(db["instructor"].rows_where("name = ? AND fsnum IS NULL", [name]))
            if existing:
                row_id = existing[0]["id"]
            else:
                row_id = db["instructor"].insert({"fsnum": None, "name": name}).last_pk

        db["section_instructor"].insert(
            {"clbid": clbid, "instructor_id": row_id},
            replace=True,
        )


def link_lookups(db, clbid, course):
    """Point this section at its shared instructor and gereq rows."""
    _link_instructors(db, clbid, course)

    # Gereqs use simple name-based lookup
    db["section_gereq"].delete_where("clbid = ?", [clbid])
    for code in course.get("gereqs") or []:
        row_id = db["gereq"].lookup({"code": code})
        db["section_gereq"].insert(
            {"clbid": clbid, "gereq_id": row_id},
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
