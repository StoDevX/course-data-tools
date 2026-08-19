"""Static lookups for decoding SIS field codes.

These live in code rather than in `../course-data/data-mappings/` so that
importing the tools does not require the data repository to be checked out.
"""

# The SIS `coursesubtype` codes. A closed set defined by the SIS itself.
course_types = {
    "L": "Lab",
    "D": "Discussion",
    "S": "Seminar",
    "T": "Topic",
    "F": "FLAC",
    "R": "Research",
    "E": "Ensemble",
}
