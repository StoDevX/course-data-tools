def parse_prerequisites(course):
    search_str = "Prereq"

    prereqs_list = [
        para[para.index(search_str) :]
        for para in course.get("description", [])
        if search_str in para
    ]

    if not prereqs_list:
        prereqs_list = [
            note[note.index(search_str) :]
            for note in course.get("notes", [])
            if search_str in note
        ]

    if prereqs_list:
        return "\n".join(prereqs_list).replace("Prerequisite: ", "")

    return False
