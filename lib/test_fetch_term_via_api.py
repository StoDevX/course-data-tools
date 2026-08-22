import pytest
from unittest.mock import patch, Mock

from .fetch_term_via_api import fetch_term_via_api, parse_api_course


SAMPLE_API_RESPONSE = {
    "results": {
        "COLUMNS": [
            "CLBID", "CRSID", "DEPT_ABBR", "COURSE_NUMBER", "COURSE_SECTION",
            "COURSE_NAME", "VARIABLE_CREDITS", "HALF_SEMESTER", "STATUS",
            "CREDITS", "PASS_NOPASS", "GROUPID", "GROUPTYPE", "YEAR",
            "SEMESTER", "TERM", "COURSE_TYPE", "ENROLL_TOTAL",
            "ENROLL_TOTAL_SR", "ENROLL_TOTAL_JR", "ENROLL_TOTAL_SO",
            "ENROLL_TOTAL_FY", "ENROLL_MAX", "ENROLL_MAX_SR", "ENROLL_MAX_JR",
            "ENROLL_MAX_SO", "ENROLL_MAX_FY", "INSTRUCTORS", "SCHED",
            "GEREQS", "NOTES"
        ],
        "DATA": [
            [
                "0000151658", "0000000016", "AFAD", "231", "A",
                "Sem: Africa/Americas", "N", "", "O",
                1.0, "N", "", "", "2023",
                "3", "20233", "R", 12,
                4, 3, 2, 3, 15, None, None, None, None,
                "21082|Iddrisu, Abdulai",
                "T|0935-1100|TB 227:::Th|0930-1050|TB 227",
                "ALS-L,MCG,MCS-G", ""
            ]
        ]
    }
}


def test_parse_api_course_extracts_basic_fields():
    """API course data is transformed into our standard format."""
    row = SAMPLE_API_RESPONSE["results"]["DATA"][0]
    cols = SAMPLE_API_RESPONSE["results"]["COLUMNS"]
    course = parse_api_course(dict(zip(cols, row)))

    assert course["clbid"] == "0000151658"
    assert course["crsid"] == "0000000016"
    assert course["department"] == "AFAD"
    assert course["number"] == 231
    assert course["section"] == "A"
    assert course["name"] == "Sem: Africa/Americas"
    assert course["credits"] == 1.0
    assert course["status"] == "O"
    assert course["term"] == 20233
    assert course["year"] == 2023
    assert course["semester"] == 3


def test_parse_api_course_extracts_enrollment_as_integers():
    """Enrollment columns are integers, not strings."""
    row = SAMPLE_API_RESPONSE["results"]["DATA"][0]
    cols = SAMPLE_API_RESPONSE["results"]["COLUMNS"]
    course = parse_api_course(dict(zip(cols, row)))

    assert course["enrolled"] == 12
    assert course["max"] == 15
    assert course["enrollment_fy"] == 3
    assert course["enrollment_so"] == 2
    assert course["enrollment_jr"] == 3
    assert course["enrollment_sr"] == 4
    assert course["max_fy"] is None
    assert course["max_so"] is None


def test_parse_api_course_parses_instructors_with_fsnum():
    """Instructors include FSNUM for stable identity."""
    row = SAMPLE_API_RESPONSE["results"]["DATA"][0]
    cols = SAMPLE_API_RESPONSE["results"]["COLUMNS"]
    course = parse_api_course(dict(zip(cols, row)))

    # instructors_full has FSNUM
    assert course["instructors_full"] == [{"fsnum": "21082", "name": "Iddrisu, Abdulai"}]
    # instructors has just names for compat with current database
    assert course["instructors"] == ["Iddrisu, Abdulai"]


def test_parse_api_course_parses_schedule():
    """Schedule is pre-parsed into offerings with normalized day/time format."""
    row = SAMPLE_API_RESPONSE["results"]["DATA"][0]
    cols = SAMPLE_API_RESPONSE["results"]["COLUMNS"]
    course = parse_api_course(dict(zip(cols, row)))

    assert course["offerings"] == [
        {"day": "Tu", "start": "09:35", "end": "11:00", "location": "TB 227"},
        {"day": "Th", "start": "09:30", "end": "10:50", "location": "TB 227"},
    ]


def test_parse_api_course_parses_gereqs():
    """GEREQs are split into a list."""
    row = SAMPLE_API_RESPONSE["results"]["DATA"][0]
    cols = SAMPLE_API_RESPONSE["results"]["COLUMNS"]
    course = parse_api_course(dict(zip(cols, row)))

    assert course["gereqs"] == ["ALS-L", "MCG", "MCS-G"]


def test_parse_api_course_handles_pass_nopass():
    """P/N flag is converted to boolean."""
    row = SAMPLE_API_RESPONSE["results"]["DATA"][0]
    cols = SAMPLE_API_RESPONSE["results"]["COLUMNS"]
    course = parse_api_course(dict(zip(cols, row)))

    assert course["pn"] is False

    # Test Y case
    row_pn = list(row)
    row_pn[cols.index("PASS_NOPASS")] = "Y"
    course_pn = parse_api_course(dict(zip(cols, row_pn)))
    assert course_pn["pn"] is True


@patch('lib.fetch_term_via_api.requests.get')
def test_fetch_term_via_api_returns_courses(mock_get):
    """API call returns parsed courses."""
    mock_response = Mock()
    mock_response.json.return_value = SAMPLE_API_RESPONSE
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    courses = list(fetch_term_via_api(20233))

    assert len(courses) == 1
    assert courses[0]["clbid"] == "0000151658"
    mock_get.assert_called_once()
    assert "terms=20233" in mock_get.call_args[0][0]
