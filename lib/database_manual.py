from sqlalchemy import Table, Column, Integer, String, Float, Boolean, MetaData, ForeignKey
from sqlalchemy.sql import select
from copy import deepcopy

metadata = MetaData()

course_to_depts = Table(
    'courses_to_depts',
    metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('department_id', Integer, ForeignKey('department.id'), primary_key=True),
)

course_to_gereqs = Table(
    'courses_to_gereqs',
    metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('gereq_id', Integer, ForeignKey('gereq.id'), primary_key=True),
)

course_to_timeslots = Table(
    'courses_to_timeslots',
    metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('timeslot_id', Integer, ForeignKey('timeslot.id'), primary_key=True),
)

course_to_locations = Table(
    'courses_to_locations',
    metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('location_id', Integer, ForeignKey('location.id'), primary_key=True),
)

course_to_instructors = Table(
    'courses_to_instructors',
    metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('instructor_id', Integer, ForeignKey('instructor.id'), primary_key=True),
)

course_to_notes = Table(
    'courses_to_notes',
    metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('note_id', Integer, ForeignKey('note.id'), primary_key=True),
)

course_to_prereqs = Table(
    'courses_to_prereqs',
    metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('prereq_id', Integer, ForeignKey('prereq.id'), primary_key=True),
)

course_to_descriptions = Table(
    'courses_to_descriptions',
    metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('description_id', Integer, ForeignKey('description.id'), primary_key=True),
)

department = Table(
    'department',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=True),
    Column('abbr', String, nullable=False),
    Column('short_abbr', String, nullable=True),
)

instructor = Table(
    'instructor',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
)

description = Table(
    'description',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('text', String),
)

note = Table(
    'note',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('text', String),
)

prereq = Table(
    'prereq',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('text', String),
)

location = Table(
    'location',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('building', String),
    Column('room', String),
)

timeslot = Table(
    'timeslot',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('sis', String),
    Column('days', String),
    Column('start', String),
    Column('end', String),
)

gereq = Table(
    'gereq',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('abbr', String),
)

course = Table(
    'course',
    metadata,

    Column('id', Integer, primary_key=True),

    Column('clbid', Integer, nullable=False),
    Column('crsid', Integer, nullable=False),
    Column('credits', Float, nullable=False),

    Column('number', Integer, nullable=True),
    Column('section', String, nullable=True),
    Column('name', String, nullable=False),
    Column('full_name', String),
    # Column('description', String),
    # Column('notes', String),
    Column('pn', Boolean),
    Column('status', String),
    Column('term', Integer),
    Column('type', String),

    Column('groupid', Integer),
    Column('grouptype', String),

    # departments=relationship('Department', secondary=course_to_depts),
    # gereqs=relationship('GeReq', secondary=course_to_gereqs),
    # times=relationship('TimeSlot', secondary=course_to_timeslots),
    # locations=relationship('Location', secondary=course_to_locations),
    # instructors=relationship('Instructor', secondary=course_to_instructors),

    Column('year', Integer),
    Column('semester', Integer),

    # Column('prerequisites', String, nullable=True),
    Column('level', String),  # course level, e.g. 2XX
)


def clean_course(source_course):
    c = deepcopy(source_course)
    c['semester'] = c['semester']
    c['year'] = c['year']
    c['term'] = c['term']
    c['level'] = str(c['level'])
    c['grouptype'] = str(c.get('grouptype', None))

    c['full_name'] = c.get('title', None)
    if 'title' in c:
        del c['title']

    if 'halfcredit' in c:
        del c['halfcredit']
    if 'revisions' in c:
        del c['revisions']

    c['departments'] = c.get('departments', [])
    c['instructors'] = c.get('instructors', [])
    c['locations'] = c.get('locations', [])
    c['times'] = c.get('times', [])
    c['gereqs'] = c.get('gereqs', [])

    return c

    # c['departments'] = [Department(abbr=d) for d in c.get('departments', [])]
    # c['instructors'] = [Instructor(name=x) for x in c.get('instructors', [])]
    # c['locations'] = [Location(name=l) for l in c.get('locations', [])]
    # c['times'] = [TimeSlot(desc=x) for x in c.get('times', [])]
    # c['gereqs'] = [GeReq(abbr=x) for x in c.get('gereqs', [])]
    # return Course(**c)


def insert_course(c, conn):
    for dept_abbr in c['departments']:
        results = conn.execute(select([department]).where(department.c.abbr == dept_abbr).limit(1))
        if not results.fetchone():
            stmt = department.insert().values(abbr=dept_abbr)
            conn.execute(stmt)
    del c['departments']

    for inst_name in c['instructors']:
        results = conn.execute(select([instructor]).where(instructor.c.name == inst_name).limit(1))
        if not results.fetchone():
            stmt = instructor.insert().values(name=inst_name)
            conn.execute(stmt)
    del c['instructors']

    for loc in c['locations']:
        results = conn.execute(select([location]).where(location.c.name == loc).limit(1))
        if not results.fetchone():
            stmt = location.insert().values(name=loc)
            conn.execute(stmt)
    del c['locations']

    for slot in c['times']:
        days, time = slot.split(' ')
        start, end = time.split('-')
        results = conn.execute(select([timeslot]).where(timeslot.c.sis == slot).limit(1))
        if not results.fetchone():
            stmt = timeslot.insert().values(sis=slot, days=days, start=start, end=end)
            conn.execute(stmt)
    del c['times']

    for ge_abbr in c['gereqs']:
        results = conn.execute(select([gereq]).where(gereq.c.abbr == ge_abbr).limit(1))
        if not results.fetchone():
            stmt = gereq.insert().values(abbr=ge_abbr)
            conn.execute(stmt)
    del c['gereqs']

    if c.get('notes', None):
        for note_text in c['notes']:
            results = conn.execute(select([note]).where(note.c.text == note_text).limit(1))
            if not results.fetchone():
                stmt = note.insert().values(text=note_text)
                conn.execute(stmt)
        del c['notes']

    if c.get('description', None):
        for desc_text in c['description']:
            results = conn.execute(select([description]).where(description.c.text == desc_text).limit(1))
            if not results.fetchone():
                stmt = description.insert().values(text=desc_text)
                conn.execute(stmt)
        del c['description']

    if c.get('prerequisites', False):
        prereq_text = c['prerequisites']
        results = conn.execute(select([prereq]).where(prereq.c.text == prereq_text).limit(1))
        if not results.fetchone():
            stmt = prereq.insert().values(text=prereq_text)
            conn.execute(stmt)
    del c['prerequisites']

    stmt = course.insert().values(**c)
    conn.execute(stmt)

# c = s.query(Course).filter(Course.year == '2018').first()
# print(c)

# print(s.query(Course).from_statement(
#     text("SELECT * FROM courses where name LIKE :name")).params(name='%Amer%').all())
