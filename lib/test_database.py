import pytest
from sqlite_utils import Database

from .database import create_schema, insert_course


def course(**overrides):
    c = {
        'clbid': '0000150738',
        'crsid': '0000000747',
        'term': 20233,
        'year': 2023,
        'semester': 3,
        'department': 'MATH',
        'number': 252,
        'section': 'A',
        'level': 200,
        'type': 'Research',
        'name': 'Abstract Algebra I',
        'credits': 1.0,
        'pn': False,
        'learningmode': 'S',
        'status': 'O',
        'enrolled': 18,
        'max': 18,
        'instructors': ['Dietz, Jill'],
    }
    c.update(overrides)
    return c


@pytest.fixture
def db():
    database = Database(memory=True)
    create_schema(database)
    return database


def test_section_is_keyed_on_clbid(db):
    insert_course(db, course())
    assert [r['clbid'] for r in db['section'].rows] == [150738]


def test_reinserting_a_course_updates_rather_than_duplicates(db):
    insert_course(db, course(name='Old Name'))
    insert_course(db, course(name='New Name'))
    rows = list(db['section'].rows)
    assert len(rows) == 1
    assert rows[0]['name'] == 'New Name'


def test_each_instructor_gets_its_own_row(db):
    insert_course(db, course(instructors=['Dietz, Jill', 'Rives, Hawken']))
    assert sorted(r['name'] for r in db['instructor'].rows) == [
        'Dietz, Jill', 'Rives, Hawken',
    ]


def test_instructors_are_shared_between_sections(db):
    insert_course(db, course(clbid='0000000001', instructors=['Dietz, Jill']))
    insert_course(db, course(clbid='0000000002', instructors=['Dietz, Jill']))
    assert len(list(db['instructor'].rows)) == 1
    assert len(list(db['section_instructor'].rows)) == 2


def test_each_gereq_gets_its_own_row(db):
    insert_course(db, course(gereqs=['WRI', 'WAC']))
    assert sorted(r['code'] for r in db['gereq'].rows) == ['WAC', 'WRI']


def test_offerings_belong_to_one_section(db):
    insert_course(db, course(offerings=[
        {'day': 'Mo', 'start': '12:55', 'end': '13:50', 'location': 'HH 429'},
        {'day': 'We', 'start': '12:55', 'end': '13:50', 'location': 'HH 429'},
    ]))
    rows = list(db['offering'].rows)
    assert len(rows) == 2
    assert {r['clbid'] for r in rows} == {150738}
    assert sorted(r['day'] for r in rows) == ['Mo', 'We']


def test_reinserting_replaces_offerings_rather_than_appending(db):
    """A rebuild must not accumulate stale offerings for a section."""
    insert_course(db, course(offerings=[
        {'day': 'Mo', 'start': '12:55', 'end': '13:50', 'location': 'HH 429'},
    ]))
    insert_course(db, course(offerings=[
        {'day': 'Tu', 'start': '09:00', 'end': '10:00', 'location': 'RNS 210'},
    ]))
    assert [r['day'] for r in db['offering'].rows] == ['Tu']


def test_reinserting_replaces_instructors_rather_than_appending(db):
    insert_course(db, course(instructors=['Dietz, Jill']))
    insert_course(db, course(instructors=['Rives, Hawken']))
    links = list(db['section_instructor'].rows)
    assert len(links) == 1
    name = {r['id']: r['name'] for r in db['instructor'].rows}
    assert name[links[0]['instructor_id']] == 'Rives, Hawken'


def test_description_list_is_joined(db):
    insert_course(db, course(description=['First para.', 'Second para.']))
    assert next(db['section'].rows)['description'] == 'First para.\nSecond para.'


def test_notes_use_the_plural_json_key(db):
    insert_course(db, course(notes=['Open to seniors.', 'Has an ACE component.']))
    row = next(db['section'].rows)
    assert row['notes'] == 'Open to seniors.\nHas an ACE component.'


def test_pass_nopass_comes_from_the_pn_flag(db):
    insert_course(db, course(clbid='0000000001', pn=True))
    insert_course(db, course(clbid='0000000002', pn=False))
    rows = {r['clbid']: r['pass_nopass'] for r in db['section'].rows}
    assert rows[1] == 1
    assert rows[2] == 0


def test_missing_optional_fields_do_not_raise(db):
    """~2.4% of courses lack department/enrolled/max; 4.7% lack learningmode."""
    sparse = course()
    for key in ('department', 'enrolled', 'max', 'learningmode',
                'section', 'title', 'number', 'notes'):
        sparse.pop(key, None)
    insert_course(db, sparse)
    row = next(db['section'].rows)
    assert row['learning_mode'] == ''
    assert row['enrolled'] is None
