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
    name_row = db['name_text'].get(rows[0]['name_id'])
    assert name_row['text'] == 'New Name'


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
    days = sorted(db['timeslot'].get(r['timeslot_id'])['day'] for r in rows)
    assert days == ['Mo', 'We']


def test_reinserting_replaces_offerings_rather_than_appending(db):
    """A rebuild must not accumulate stale offerings for a section."""
    insert_course(db, course(offerings=[
        {'day': 'Mo', 'start': '12:55', 'end': '13:50', 'location': 'HH 429'},
    ]))
    insert_course(db, course(offerings=[
        {'day': 'Tu', 'start': '09:00', 'end': '10:00', 'location': 'RNS 210'},
    ]))
    rows = list(db['offering'].rows)
    assert len(rows) == 1
    assert db['timeslot'].get(rows[0]['timeslot_id'])['day'] == 'Tu'


def test_reinserting_replaces_instructors_rather_than_appending(db):
    insert_course(db, course(instructors=['Dietz, Jill']))
    insert_course(db, course(instructors=['Rives, Hawken']))
    links = list(db['section_instructor'].rows)
    assert len(links) == 1
    name = {r['id']: r['name'] for r in db['instructor'].rows}
    assert name[links[0]['instructor_id']] == 'Rives, Hawken'


def test_description_list_is_joined(db):
    """Description paragraphs are joined before interning."""
    insert_course(db, course(description=['First para.', 'Second para.']))
    section = next(db['section'].rows)
    desc_row = db['description_text'].get(section['description_id'])
    assert desc_row['text'] == 'First para.\nSecond para.'


def test_notes_use_the_plural_json_key(db):
    """Notes paragraphs are joined before interning."""
    insert_course(db, course(notes=['Open to seniors.', 'Has an ACE component.']))
    section = next(db['section'].rows)
    notes_row = db['notes_text'].get(section['notes_id'])
    assert notes_row['text'] == 'Open to seniors.\nHas an ACE component.'


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


# --- Interned text tables (compression) ---

def test_description_is_interned_into_lookup_table(db):
    """Descriptions live in description_text; section holds an FK."""
    insert_course(db, course(description=['First para.', 'Second para.']))
    assert 'description_text' in db.table_names()
    texts = list(db['description_text'].rows)
    assert len(texts) == 1
    assert texts[0]['text'] == 'First para.\nSecond para.'


def test_identical_descriptions_share_one_row(db):
    """Two sections with the same description should reference the same row."""
    desc = ['Shared description.']
    insert_course(db, course(clbid='0000000001', description=desc))
    insert_course(db, course(clbid='0000000002', description=desc))
    assert len(list(db['description_text'].rows)) == 1
    sections = list(db['section'].rows)
    assert sections[0]['description_id'] == sections[1]['description_id']


def test_empty_description_stores_null_not_empty_string(db):
    """No description means NULL FK, not a row containing empty string."""
    insert_course(db, course(description=None))
    row = next(db['section'].rows)
    assert row['description_id'] is None
    assert len(list(db['description_text'].rows)) == 0


def test_name_is_interned_into_lookup_table(db):
    """Names live in name_text; section holds an FK."""
    insert_course(db, course(name='Abstract Algebra I'))
    assert 'name_text' in db.table_names()
    texts = list(db['name_text'].rows)
    assert len(texts) == 1
    assert texts[0]['text'] == 'Abstract Algebra I'


def test_identical_names_share_one_row(db):
    insert_course(db, course(clbid='0000000001', name='Calculus I'))
    insert_course(db, course(clbid='0000000002', name='Calculus I'))
    assert len(list(db['name_text'].rows)) == 1


def test_notes_is_interned_into_lookup_table(db):
    """Notes live in notes_text; section holds an FK."""
    insert_course(db, course(notes=['Open to seniors.']))
    assert 'notes_text' in db.table_names()
    section = next(db['section'].rows)
    note_row = db['notes_text'].get(section['notes_id'])
    assert note_row['text'] == 'Open to seniors.'


def test_title_is_interned_into_lookup_table(db):
    """Titles live in title_text; section holds an FK."""
    insert_course(db, course(title='MATH 252: Abstract Algebra I'))
    assert 'title_text' in db.table_names()
    section = next(db['section'].rows)
    title_row = db['title_text'].get(section['title_id'])
    assert title_row['text'] == 'MATH 252: Abstract Algebra I'


# --- Interned offering data ---

def test_location_is_interned_into_lookup_table(db):
    """Locations live in location; offering holds an FK."""
    insert_course(db, course(offerings=[
        {'day': 'Mo', 'start': '12:55', 'end': '13:50', 'location': 'HH 429'},
    ]))
    assert 'location' in db.table_names()
    locations = list(db['location'].rows)
    assert len(locations) == 1
    assert locations[0]['name'] == 'HH 429'


def test_identical_locations_share_one_row(db):
    insert_course(db, course(offerings=[
        {'day': 'Mo', 'start': '12:55', 'end': '13:50', 'location': 'HH 429'},
        {'day': 'We', 'start': '12:55', 'end': '13:50', 'location': 'HH 429'},
    ]))
    assert len(list(db['location'].rows)) == 1


def test_timeslot_is_interned_into_lookup_table(db):
    """Timeslots (day+start+end) live in timeslot; offering holds an FK."""
    insert_course(db, course(offerings=[
        {'day': 'Mo', 'start': '12:55', 'end': '13:50', 'location': 'HH 429'},
    ]))
    assert 'timeslot' in db.table_names()
    slots = list(db['timeslot'].rows)
    assert len(slots) == 1
    assert slots[0]['day'] == 'Mo'
    assert slots[0]['start'] == '12:55'
    assert slots[0]['end'] == '13:50'


def test_identical_timeslots_share_one_row(db):
    """Two offerings at the same time (different locations) share one timeslot."""
    insert_course(db, course(offerings=[
        {'day': 'Mo', 'start': '09:00', 'end': '10:00', 'location': 'HH 429'},
        {'day': 'Mo', 'start': '09:00', 'end': '10:00', 'location': 'RNS 210'},
    ]))
    assert len(list(db['timeslot'].rows)) == 1
    assert len(list(db['location'].rows)) == 2


# --- Compatibility VIEW ---

def test_section_full_view_joins_interned_text(db):
    """section_full VIEW joins all interned text for backwards-compatible queries."""
    insert_course(db, course(
        name='Abstract Algebra I',
        title='MATH 252: Abstract Algebra I',
        description=['First para.', 'Second para.'],
        notes=['Open to seniors.'],
    ))
    assert 'section_full' in db.view_names()
    rows = list(db['section_full'].rows)
    assert len(rows) == 1
    row = rows[0]
    assert row['name'] == 'Abstract Algebra I'
    assert row['title'] == 'MATH 252: Abstract Algebra I'
    assert row['description'] == 'First para.\nSecond para.'
    assert row['notes'] == 'Open to seniors.'


def test_offering_full_view_joins_timeslot_and_location(db):
    """offering_full VIEW joins timeslot and location for backwards-compatible queries."""
    insert_course(db, course(offerings=[
        {'day': 'Mo', 'start': '12:55', 'end': '13:50', 'location': 'HH 429'},
    ]))
    assert 'offering_full' in db.view_names()
    rows = list(db['offering_full'].rows)
    assert len(rows) == 1
    row = rows[0]
    assert row['day'] == 'Mo'
    assert row['start'] == '12:55'
    assert row['end'] == '13:50'
    assert row['location'] == 'HH 429'
