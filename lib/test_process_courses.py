import pytest

from . import data
from .process_courses import clean_course


@pytest.fixture(autouse=True)
def stub_course_types(monkeypatch):
    """The real mapping is owned by the course-data repo, which these unit
    tests do not require a checkout of."""
    monkeypatch.setattr(data, 'course_types', lambda: {'R': 'Research'})


def base_course(**overrides):
    """A minimal course dict shaped like xmltodict output from the SIS."""
    course = {
        'clbid': '0000150738',
        'crsid': '0000000747',
        'coursestatus': 'O',
        'deptname': 'MATH',
        'coursenumber': '252',
        'coursesection': 'A',
        'coursesubtype': 'R',
        'coursename': 'Abstract Algebra I',
        'pn': 'N',
        'notes': None,
        'instructors': (
            '<a class="sis-nounderline" '
            'href="JavaScript:sis_facinfo_openwindow(\'0000205\')">Dietz, Jill </a>'
        ),
        'credits': '1.00',
        'gereqs': None,
        'enroll': '18',
        'max': '18',
        'firstyear': None,
        'sophomore': None,
        'junior': None,
        'senior': None,
        'meetingtimes': None,
        'meetinglocations': None,
        'learningmode': 'S',
        'varcredits': 'N',
        'term': 20233,
        'title': None,
        'description': None,
    }
    course.update(overrides)
    return course


def test_learningmode_passes_through():
    assert clean_course(base_course(learningmode='S'))['learningmode'] == 'S'
    assert clean_course(base_course(learningmode='A'))['learningmode'] == 'A'


def test_empty_learningmode_becomes_empty_string():
    """An empty tag means "All Learning Modes" and must survive as a value."""
    assert clean_course(base_course(learningmode=None))['learningmode'] == ''


def test_missing_learningmode_becomes_empty_string():
    """Terms before ~2020 have no learningmode tag at all."""
    course = base_course()
    del course['learningmode']
    assert clean_course(course)['learningmode'] == ''


def test_pn_flag_is_a_real_boolean():
    assert clean_course(base_course(pn='Y'))['pn'] is True
    assert clean_course(base_course(pn='N'))['pn'] is False
