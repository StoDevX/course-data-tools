def insert_course(db, course):
    # formatting and validation
    description = course.get('description')[0] if len(course.get('description') or []) else ''
    gereqs = ",".join(course.get("gereqs", []))
    instructors = ",".join(course["instructors"])
    note = "".join(course.get("note", []))
    offerings = get_offerings(course)
    pass_nopass = 1 if "Pass or No Pass (P/N) only" in description else 0

    db["section"].insert({
        "clbid": int(course["clbid"]),
        "crsid": int(course["crsid"]),
        "credits": course["credits"],
        "learning_mode": course["learningmode"],
        "note": note,
        "pass_nopass": pass_nopass,
        "term": str(course["term"]),
        "title": course.get("title", ""),
        "year": int(course["year"]),
        }, pk="id"
    ).m2m("description", {
        "content": description
        }, pk="id"
    ).m2m("instructor", {
        "name": instructors,
        "fsnum": "",
        }, pk="id"
    ).m2m("enrollment", {
        "status": course["status"],
        "max": course["max"],
        "total": course["enrolled"],
        "firstyear": course.get("firstyear"),
        "sophomore": course.get("sophomore"),
        "junior": course.get("junior"),
        "senior": course.get("senior"),
        }, pk="id"
    ).m2m("countstoward", {
        "gereq": gereqs,
        "corereq": "",
        "major": "",
        "concentration": "",
        }, pk="id"
    ).m2m("offerings", offerings, pk="id")


def build_offering(data):
    return {
        "location": data["location"],
        "days": data["day"],
        "start": data["start"],
        "end": data["end"]
    }


def get_offerings(course):
    course_offerings = course["offerings"] if len(course.get("offerings", [])) else []
    offerings = [build_offering(data) for data in course_offerings if len(course_offerings)]
    return offerings


def tracer(sql, params):
    print(f'SQL: {sql} - params: {params}')
