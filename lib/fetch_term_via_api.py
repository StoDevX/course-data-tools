"""Fetch course data from the SIS classlab API.

The API at api/classlab.cfc?method=search returns richer data than the XML feed:
- CRSID per section (stable course identity)
- FSNUM with instructor names (stable instructor identity)
- Pre-parsed schedules (day|start|end|location)
- Integer enrollment columns
"""
import requests


API_URL = "https://sis.stolaf.edu/sis/api/classlab.cfc"


def fetch_term_via_api(term):
    """Fetch all courses for a term from the classlab API.

    Yields dicts in our standard course format, one per section.
    """
    url = f"{API_URL}?method=search&terms={term}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    results = data.get("results", {})
    columns = results.get("COLUMNS", [])
    rows = results.get("DATA", [])

    for row in rows:
        yield parse_api_course(dict(zip(columns, row)))


def parse_api_course(raw):
    """Transform an API row dict into our standard course format."""
    term = int(raw["TERM"])

    course = {
        "clbid": raw["CLBID"],
        "crsid": raw["CRSID"],
        "department": raw["DEPT_ABBR"],
        "number": _parse_number(raw["COURSE_NUMBER"]),
        "section": raw["COURSE_SECTION"] or None,
        "name": raw["COURSE_NAME"],
        "credits": float(raw["CREDITS"]) if raw["CREDITS"] else None,
        "status": raw["STATUS"],
        "term": term,
        "year": int(raw["YEAR"]),
        "semester": int(raw["SEMESTER"]),
        "pn": raw["PASS_NOPASS"] == "Y",
        "type": raw["COURSE_TYPE"],
        "enrolled": raw["ENROLL_TOTAL"],
        "max": raw["ENROLL_MAX"],
        "enrollment_fy": raw["ENROLL_TOTAL_FY"],
        "enrollment_so": raw["ENROLL_TOTAL_SO"],
        "enrollment_jr": raw["ENROLL_TOTAL_JR"],
        "enrollment_sr": raw["ENROLL_TOTAL_SR"],
        "max_fy": raw["ENROLL_MAX_FY"],
        "max_so": raw["ENROLL_MAX_SO"],
        "max_jr": raw["ENROLL_MAX_JR"],
        "max_sr": raw["ENROLL_MAX_SR"],
    }

    # Compute level from number
    if isinstance(course["number"], int):
        course["level"] = (course["number"] // 100) * 100
    else:
        course["level"] = 0

    # Parse instructors: "21082|Iddrisu, Abdulai:::21083|Smith, John"
    if raw["INSTRUCTORS"]:
        parsed = _parse_instructors(raw["INSTRUCTORS"])
        course["instructors_full"] = parsed  # with FSNUM
        course["instructors"] = [i["name"] for i in parsed]  # just names for compat

    # Parse schedule: "T|0935-1100|TB 227:::Th|0930-1050|TB 227"
    if raw["SCHED"]:
        course["offerings"] = _parse_schedule(raw["SCHED"])

    # Parse gereqs: "ALS-L,MCG,MCS-G"
    if raw["GEREQS"]:
        course["gereqs"] = raw["GEREQS"].split(",")

    # Notes
    if raw["NOTES"]:
        course["notes"] = raw["NOTES"].split("\n")

    return course


def _parse_number(num_str):
    """Parse course number, returning int if numeric."""
    try:
        return int(num_str)
    except (ValueError, TypeError):
        return num_str


def _parse_instructors(instructors_str):
    """Parse 'FSNUM|Name:::FSNUM|Name' into list of dicts."""
    result = []
    for part in instructors_str.split(":::"):
        if "|" in part:
            fsnum, name = part.split("|", 1)
            result.append({"fsnum": fsnum, "name": name})
        elif part:
            result.append({"fsnum": None, "name": part})
    return result


DAY_MAP = {
    "M": "Mo", "T": "Tu", "W": "We", "Th": "Th", "F": "Fr", "Sa": "Sa", "Su": "Su"
}


def _normalize_time(t):
    """Convert '0935' to '09:35'."""
    if len(t) == 4 and t.isdigit():
        return f"{t[:2]}:{t[2:]}"
    return t


def _parse_schedule(sched_str):
    """Parse 'Day|Start-End|Location:::...' into list of offering dicts."""
    result = []
    for part in sched_str.split(":::"):
        pieces = part.split("|")
        if len(pieces) >= 3:
            day = pieces[0]
            times = pieces[1]
            location = pieces[2] if len(pieces) > 2 else ""

            if "-" in times:
                start, end = times.split("-", 1)
            else:
                start = end = times

            result.append({
                "day": DAY_MAP.get(day, day),
                "start": _normalize_time(start),
                "end": _normalize_time(end),
                "location": location,
            })
    return result
