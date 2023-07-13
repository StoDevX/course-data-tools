import sqlite_utils

from .ensure_dir_exists import ensure_dir_exists


db = sqlite_utils.Database("catalog.db")

def save_data(data, filepath):
    ensure_dir_exists(filepath)
    with open(filepath, mode='w+', newline='\n') as outfile:
        outfile.write(data)


def write_to_database(courses):
    for course in courses:
        insert_course_data(course)

    extract_columns_post_insertion()


def extract_columns_post_insertion():
    # section_description
    db["section"].extract("description", table="section_description", fk_column="section_description_id")

    # section_instructors
    db["section"].extract("instructors", table="section_instructors", fk_column="section_instructors_id")

    # section_course
    db["section"].extract(["crsid", "department_1", "department_2", "name", "number", "repeat" ,"type",], table="section_course", fk_column="section_course_id")

    # section_enrollment
    db["section"].extract(["status", "max", "total", "firstyear", "sophomore", "junior", "senior"], table="section_enrollment", fk_column="section_enrollment_id")

    # section_countstowards
    db["section"].extract(["gereq", "corereq", "major", "concentration"], table="section_countstowards", fk_column="section_countstowards_id")


def insert_course_data(course):
    # formatting and validation
    description = course.get('description')[0] if len(course.get('description') or []) else ''
    gereqs = ",".join(course.get("gereqs", []))
    instructors = "".join(course["instructors"])
    note = "".join(course.get("note", []))
    offerings = course["offerings"] if len(course.get("offerings", [])) else []
    pass_nopass = 1 if "Pass or No Pass (P/N) only" in description else 0

    # Insert into the 'section' table
    section_row = {
        # section
        "clbid": course["clbid"],
        "course_id": course["crsid"],
        "credits": course["credits"],
        "description": description,
        "instructors": instructors,
        "learning_mode": course["learningmode"],
        "note": note,
        "pass_nopass": pass_nopass,
        "term": str(course["term"]),
        "title": course.get("title", ""),
        "year": int(course["year"]),

        # course
        "crsid": course["crsid"],
        "department_1": course["department"],
        "department_2": "",
        "level": course["level"],
        "name": course["name"],
        "number": course["number"],
        "repeat": "",
        "type": course["type"],

        # enrollment
        "status": course["status"],
        "max": course["max"],
        "total": course["enrolled"],
        "firstyear": course.get("firstyear"),
        "sophomore": course.get("sophomore"),
        "junior": course.get("junior"),
        "senior": course.get("senior"),

        # countstowards
        "gereq": gereqs,
        "corereq": "",
        "major": "",
        "concentration": "",
    }
    db["section"].insert(section_row, pk="id")

    # Insert into the 'meeting' table
    for offering in offerings:
        meeting_row = {
            "clbid": course["clbid"],
            "location": offering["location"],
            "days": offering["day"],
            "start": offering["start"],
            "end": offering["end"]
        }
        db["meeting"].insert(meeting_row, pk="id")
