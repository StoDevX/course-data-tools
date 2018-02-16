from sqlalchemy import *
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

course_to_depts = Table(
    'courses_to_depts',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('department_id', Integer, ForeignKey('department.id'), primary_key=True)
)

course_to_gereqs = Table(
    'courses_to_gereqs',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('gereq_id', Integer, ForeignKey('gereq.id'), primary_key=True)
)

course_to_timeslots = Table(
    'courses_to_timeslots',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('timeslot_id', Integer, ForeignKey('timeslot.id'), primary_key=True)
)

course_to_locations = Table(
    'courses_to_locations',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('location_id', Integer, ForeignKey('location.id'), primary_key=True)
)

course_to_instructors = Table(
    'courses_to_instructors',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('instructor_id', Integer, ForeignKey('instructor.id'), primary_key=True)
)

course_to_notes = Table(
    'courses_to_notes',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('note_id', Integer, ForeignKey('note.id'), primary_key=True),
)

course_to_prereqs = Table(
    'courses_to_prereqs',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('prerequisite_id', Integer, ForeignKey('prerequisite.id'), primary_key=True),
)

course_to_descriptions = Table(
    'courses_to_descriptions',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('description_id', Integer, ForeignKey('description.id'), primary_key=True),
)


class Department(Base):
    __tablename__ = 'department'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    abbr = Column(String, nullable=False)
    short_abbr = Column(String, nullable=True)

    def __repr__(self):
        return f"<Department(abbr='{self.abbr}')>"


class Instructor(Base):
    __tablename__ = 'instructor'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f"<Instructor('{self.name}')>"


class Description(Base):
    __tablename__ = 'description'

    id = Column(Integer, primary_key=True)
    text = Column(String)

    def __repr__(self):
        return f"<Description('{self.text}')>"


class Note(Base):
    __tablename__ = 'note'

    id = Column(Integer, primary_key=True)
    text = Column(String)

    def __repr__(self):
        return f"<Note('{self.text}')>"


class Prerequisite(Base):
    __tablename__ = 'prerequisite'

    id = Column(Integer, primary_key=True)
    text = Column(String)

    def __repr__(self):
        return f"<Prerequisite('{self.text}')>"


class Type(Base):
    __tablename__ = 'type'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f"<Type('{self.name}')>"


class Group(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    gid = Column(Integer)
    type = Column(String)

    def __repr__(self):
        return f"<Group(id='{self.gid}' type='{self.type}')>"


class Status(Base):
    __tablename__ = 'status'

    id = Column(Integer, primary_key=True)
    status = Column(String)

    def __repr__(self):
        return f"<Status('{self.status}')>"


class Location(Base):
    __tablename__ = 'location'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    building = Column(String)
    room = Column(String)

    def __repr__(self):
        return f"<Location('{self.name}')>"


class TimeSlot(Base):
    __tablename__ = 'timeslot'

    id = Column(Integer, primary_key=True)
    sis = Column(String)
    days = Column(String)
    start = Column(String)
    end = Column(String)

    def __repr__(self):
        return f"<Time('{self.sis}')>"


class GeReq(Base):
    __tablename__ = 'gereq'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    abbr = Column(String)

    def __repr__(self):
        return f"<GeReq('{self.name}')>"


class Course(Base):
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True)

    clbid = Column(Integer, nullable=False)
    crsid = Column(Integer, nullable=False)
    credits = Column(Float, nullable=False)

    number = Column(Integer, nullable=True)
    section = Column(String, nullable=True)
    name = Column(String, nullable=False)
    full_name = Column(String)
    # description = Column(String)
    # notes = Column(String)
    pn = Column(Boolean)
    # status = Column(String)
    term = Column(Integer)
    # type = Column(String)

    # groupid = Column(Integer)
    # grouptype = Column(String)

    year = Column(Integer)
    semester = Column(Integer)

    # prerequisites = Column(String, nullable=True)
    level = Column(String)  # course level, e.g. 2XX

    # many-to-many relationships
    departments = relationship('Department', secondary=course_to_depts)
    gereqs = relationship('GeReq', secondary=course_to_gereqs)
    times = relationship('TimeSlot', secondary=course_to_timeslots)
    locations = relationship('Location', secondary=course_to_locations)
    instructors = relationship('Instructor', secondary=course_to_instructors)
    prerequisites = relationship('Prerequisite', secondary=course_to_prereqs)
    notes = relationship('Note', secondary=course_to_notes)
    descriptions = relationship('Description', secondary=course_to_descriptions)

    # many-to-one relationships
    type_id = Column(Integer, ForeignKey('type.id'))
    type = relationship("Type")

    group_id = Column(Integer, ForeignKey('group.id'))
    group = relationship("Group")

    status_id = Column(Integer, ForeignKey('status.id'))
    status = relationship("Status")

    def __repr__(self):
        depts = ','.join([repr(d) for d in self.departments])
        locs = ','.join([repr(d) for d in self.locations])
        clbid = self.clbid
        year = self.year
        semester = self.semester
        number = self.number
        return f"<Course(clbid='{clbid}', term='{year}-{semester}', depts='{depts}', number='{number}', loc='{locs}')>"


def lookup_or_create(session):
    def do_things(kind, filters, creation):
        query = session.query(kind).filter(*filters)
        if kind == Location:
            print()
            print(str(query))
            print(creation)
            print(query.all())
        extant = query.first()
        if extant:
            if kind == Location:
                print('found')
                print()
            return extant
        if kind == Location:
            print('created')
            print()
        item = kind(**creation)
        session.add(item)
        return item

    return do_things


def clean_course(c, session):
    c['semester'] = str(c['semester'])
    c['year'] = str(c['year'])
    c['term'] = str(c['term'])
    c['level'] = str(c['level'])
    c['grouptype'] = str(c.get('grouptype', None))

    c['full_name'] = c.get('title', None)
    if 'title' in c:
        del c['title']

    if 'halfcredit' in c:
        del c['halfcredit']
    if 'revisions' in c:
        del c['revisions']

    make = lookup_or_create(session)

    c['departments'] = [make(Department, [Department.abbr == d], {'abbr': d}) for d in c['departments']]
    c['instructors'] = [make(Instructor, [Instructor.name == x], {'name': x}) for x in c['instructors']]
    c['locations'] = [make(Location, [Location.name == l], {'name': l}) for l in c.get('locations', [])]
    c['times'] = [make(TimeSlot, [TimeSlot.sis == time], {'sis': time}) for time in c.get('times', [])]
    c['gereqs'] = [make(GeReq, [GeReq.abbr == ge], {'abbr': ge}) for ge in c.get('gereqs', [])]

    if 'description' in c:
        c['descriptions'] = [make(Description, [Description.text == x], {'text': x}) for x in c.get('description', [])]
        del c['description']

    c['notes'] = [make(Note, [Note.text == x], {'text': x}) for x in c.get('notes', [])]

    if c['prerequisites'] is False:
        del c['prerequisites']
    else:
        prereqs = c.get('prerequisites', None)
        if not prereqs:
            del c['prerequisites']
        else:
            c['prerequisites'] = [make(Prerequisite, [Prerequisite.text == prereqs], {'text': prereqs})]

    if 'groupid' in c:
        gid = c['groupid']
        if 'grouptype' in c:
            t = c['grouptype']
            c['group'] = make(Group, [Group.gid == gid, Group.type == t], {'gid': gid, 'type': t})
            del c['groupid']
            del c['grouptype']
        else:
            c['group'] = make(Group, [Group.gid == gid], {'gid': gid})
            del c['groupid']
    elif 'grouptype' in c:
        t = c['grouptype']
        c['group'] = make(Group, [Group.type == t], {'type': t})
        del c['grouptype']

    if 'type' in c:
        name = c['type']
        c['type'] = make(Type, [Type.name == name], {'name': name})

    if 'status' in c:
        status = c['status']
        c['status'] = make(Status, [Status.status == status], {'status': status})

    item = Course(**c)

    # session.add(item)
    # session.commit()

    return item
