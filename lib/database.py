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

course_to_offerings = Table(
    'courses_to_offerings',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('offering_id', Integer, ForeignKey('offering.id'), primary_key=True)
)

# course_to_timeslots = Table(
#     'courses_to_timeslots',
#     Base.metadata,
#     Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
#     Column('timeslot_id', Integer, ForeignKey('timeslot.id'), primary_key=True)
# )
#
# course_to_locations = Table(
#     'courses_to_locations',
#     Base.metadata,
#     Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
#     Column('location_id', Integer, ForeignKey('location.id'), primary_key=True)
# )

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


class Offering(Base):
    __tablename__ = 'offering'

    id = Column(Integer, primary_key=True)
    timeslot_id = Column(Integer, ForeignKey('timeslot.id'))
    timeslot = relationship(TimeSlot)
    location_id = Column(Integer, ForeignKey('location.id'))
    location = relationship(Location)

    def __repr__(self):
        return f"<Offering(time='{self.timeslot}', location='{self.location}')>"


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
    # times = relationship('TimeSlot', secondary=course_to_timeslots)
    # locations = relationship('Location', secondary=course_to_locations)
    instructors = relationship('Instructor', secondary=course_to_instructors)
    prerequisites = relationship('Prerequisite', secondary=course_to_prereqs)
    notes = relationship('Note', secondary=course_to_notes)
    descriptions = relationship('Description', secondary=course_to_descriptions)
    offerings = relationship('Offering', secondary=course_to_offerings)

    # many-to-one relationships
    type_id = Column(Integer, ForeignKey('type.id'))
    type = relationship("Type")

    group_id = Column(Integer, ForeignKey('group.id'))
    group = relationship("Group")

    status_id = Column(Integer, ForeignKey('status.id'))
    status = relationship("Status")

    def __repr__(self):
        depts = ','.join([repr(d) for d in self.departments])
        # locs = ','.join([repr(d) for d in self.locations])
        when = ','.join([repr(d) for d in self.offerings])
        clbid = self.clbid
        year = self.year
        semester = self.semester
        number = self.number
        return f"<Course(clbid='{clbid}', term='{year}-{semester}', depts='{depts}', number='{number}', when='{when}')>"


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

    c['departments'] = [Department(abbr=d)
                        if session.query(Department).filter(Department.abbr == d).first() is None
                        else session.query(Department).filter(Department.abbr == d).first()
                        for d in c['departments']]
    c['instructors'] = [Instructor(name=name)
                        if session.query(Instructor).filter(Instructor.name == name).first() is None
                        else session.query(Instructor).filter(Instructor.name == name).first()
                        for name in c.get('instructors', [])]
    c['gereqs'] = [GeReq(abbr=abbr)
                   if session.query(GeReq).filter(GeReq.abbr == abbr).first() is None
                   else session.query(GeReq).filter(GeReq.abbr == abbr).first()
                   for abbr in c.get('gereqs', [])]

    c['offerings'] = []
    for time, location in zip(c.get('times', []), c.get('locations', [])):
        time_ = session.query(TimeSlot).filter(TimeSlot.sis == time).first()
        location_ = session.query(Location).filter(Location.name == location).first()

        if time_ and location_:
            offering_ = session.query(Offering) \
                .filter(Offering.timeslot_id == time_.id) \
                .filter(Offering.location_id == location_.id) \
                .first()
        else:
            offering_ = None

        if offering_:
            c['offerings'].append(offering_)
        else:
            ts = time_ if time_ else TimeSlot(sis=time)
            loc = location_ if location_ else Location(name=location)
            item = Offering(timeslot=ts, location=loc)
            c['offerings'].append(item)

    if 'locations' in c:
        del c['locations']
    if 'times' in c:
        del c['times']

    if 'description' in c:
        c['descriptions'] = [Description(text=text)
                             if session.query(Description).filter(Description.text == text).first() is None
                             else session.query(Description).filter(Description.text == text).first()
                             for text in c.get('description', [])]
        del c['description']

    c['notes'] = [Note(text=text)
                  if session.query(Note).filter(Note.text == text).first() is None
                  else session.query(Note).filter(Note.text == text).first()
                  for text in c.get('notes', [])]

    if c['prerequisites'] is False:
        del c['prerequisites']
    else:
        prereqs = c.get('prerequisites', None)
        if not prereqs:
            del c['prerequisites']
        else:
            prereq = Prerequisite(text=prereqs) \
                if session.query(Prerequisite).filter(Prerequisite.text == prereqs).first() is None \
                else session.query(Prerequisite).filter(Prerequisite.text == prereqs).first()
            c['prerequisites'] = [prereq]

    if 'groupid' in c:
        gid = c['groupid']
        if 'grouptype' in c:
            t = c['grouptype']
            c['group'] = Group(gid=gid, type=t) \
                if session.query(Group).filter(Group.gid == gid).filter(Group.type == t).first() is None \
                else session.query(Group).filter(Group.gid == gid).filter(Group.type == t).first()
            del c['groupid']
            del c['grouptype']
        else:
            c['group'] = Group(gid=gid) \
                if session.query(Group).filter(Group.gid == gid).first() is None \
                else session.query(Group).filter(Group.gid == gid).first()
            del c['groupid']
    elif 'grouptype' in c:
        t = c['grouptype']
        c['group'] = Group(type=t) \
            if session.query(Group).filter(Group.type == t).first() is None \
            else session.query(Group).filter(Group.type == t).first()
        del c['grouptype']

    if 'type' in c:
        name = c['type']
        c['type'] = Type(name=name) \
            if session.query(Type).filter(Type.name == name).first() is None \
            else session.query(Type).filter(Type.name == name).first()

    if 'status' in c:
        status = c['status']
        c['status'] = Status(status=status) \
            if session.query(Status).filter(Status.status == status).first() is None \
            else session.query(Status).filter(Status.status == status).first()

    return Course(**c)
