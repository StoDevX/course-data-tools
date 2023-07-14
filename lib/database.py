def insert_course(db, course):
    # formatting and validation
    description = course.get('description')[0] if len(course.get('description') or []) else ''
    gereqs = ",".join(course.get("gereqs", []))
    instructors = ",".join(course["instructors"])
    note = "".join(course.get("note", []))
    offerings = course["offerings"] if len(course.get("offerings", [])) else []
    pass_nopass = 1 if "Pass or No Pass (P/N) only" in description else 0

    # Insert into the 'section' table
    section_row = {
        "clbid": int(course["clbid"]),
        "crsid": int(course["crsid"]),
        "credits": course["credits"],
        "learning_mode": course["learningmode"],
        "note": note,
        "pass_nopass": pass_nopass,
        "term": str(course["term"]),
        "title": course.get("title", ""),
        "year": int(course["year"]),
    }

    db["section"].insert(section_row, pk="id").m2m(
        "course", {
            "crsid": int(course["crsid"]),
            "department_1": course["department"],
            "department_2": "",
            "level": course["level"],
            "name": course["name"],
            "number": course["number"],
            "repeat": "",
            "type": course["type"],
        }, pk="id").m2m(
        "description", {
            "content": description,
        }, pk="id").m2m(
        "instructors", {
            "name": instructors,
            "fsnum": "",
        }, pk="id").m2m(
        "enrollment", {
            "status": course["status"],
            "max": course["max"],
            "total": course["enrolled"],
            "firstyear": course.get("firstyear"),
            "sophomore": course.get("sophomore"),
            "junior": course.get("junior"),
            "senior": course.get("senior"),
        }, pk="id").m2m(
        "countstowards", {
            "gereq": gereqs,
            "corereq": "",
            "major": "",
            "concentration": "",
        }, pk="id")

    # Insert into the 'meeting' table
    for offering in offerings:
        meeting_row = {
            "clbid": int(course["clbid"]),
            "location": offering["location"],
            "days": offering["day"],
            "start": offering["start"],
            "end": offering["end"]
        }
        db["meeting"].insert(meeting_row, pk="id")


def tracer(sql, params):
    print(f'SQL: {sql} - params: {params}')
