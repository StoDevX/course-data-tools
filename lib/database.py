from sqlalchemy import *
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

course_to_depts = Table('courses_to_depts', Base.metadata,
                        Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
                        Column('department_id', Integer, ForeignKey('departments.id'), primary_key=True))

course_to_gereqs = Table('courses_to_gereqs', Base.metadata,
                         Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
                         Column('gereq_id', Integer, ForeignKey('gereqs.id'), primary_key=True))

course_to_timeslots = Table('courses_to_timeslots', Base.metadata,
                            Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
                            Column('timeslot_id', Integer, ForeignKey('timeslots.id'), primary_key=True))

course_to_locations = Table('courses_to_locations', Base.metadata,
                            Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
                            Column('location_id', Integer, ForeignKey('locations.id'), primary_key=True))

course_to_instructors = Table('courses_to_instructors', Base.metadata,
                              Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
                              Column('instructor_id', Integer, ForeignKey('instructors.id'), primary_key=True))


class Department(Base):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    abbr = Column(String, nullable=False)
    short_abbr = Column(String, nullable=True)

    def __repr__(self):
        return f"<Department(abbr='{self.abbr}')>"


class Instructor(Base):
    __tablename__ = 'instructors'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f"<Instructor('{self.name}')>"


class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    building = Column(String)
    room = Column(String)

    def __repr__(self):
        return f"<Location('{self.name}')>"


class TimeSlot(Base):
    __tablename__ = 'timeslots'

    id = Column(Integer, primary_key=True)
    desc = Column(String)
    days = Column(String)
    start = Column(String)
    end = Column(String)

    def __repr__(self):
        return f"<Time('{self.desc}')>"


class GeReq(Base):
    __tablename__ = 'gereqs'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    abbr = Column(String)

    def __repr__(self):
        return f"<GeReq('{self.name}')>"


class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)

    clbid = Column(Integer, nullable=False)
    crsid = Column(Integer, nullable=False)
    credits = Column(Float, nullable=False)

    number = Column(Integer, nullable=True)
    section = Column(String, nullable=True)
    name = Column(String, nullable=False)
    full_name = Column(String)
    description = Column(String)
    notes = Column(String)
    pn = Column(Boolean)
    status = Column(String)
    term = Column(String)
    type = Column(String)

    groupid = Column(Integer)
    grouptype = Column(String)

    departments = relationship('Department', secondary=course_to_depts)
    gereqs = relationship('GeReq', secondary=course_to_gereqs)
    times = relationship('TimeSlot', secondary=course_to_timeslots)
    locations = relationship('Location', secondary=course_to_locations)
    instructors = relationship('Instructor', secondary=course_to_instructors)

    year = Column(String)
    semester = Column(String)

    prerequisites = Column(String, nullable=True)
    level = Column(String)  # course level, e.g. 2XX

    def __repr__(self):
        depts = ','.join([repr(d) for d in self.departments])
        clbid = self.clbid
        year = self.year
        semester = self.semester
        number = self.number
        return f"<Course(clbid='{clbid}', term='{year}-{semester}', depts='{depts}', number='{number}')>"


def clean_course(c):
    c['semester'] = str(c['semester'])
    c['year'] = str(c['year'])
    c['term'] = str(c['term'])
    c['level'] = str(c['level'])
    c['description'] = str(c.get('description', None))
    c['grouptype'] = str(c.get('grouptype', None))
    c['notes'] = str(c.get('notes', None))
    c['full_name'] = c.get('title', None)
    if 'title' in c:
        del c['title']
    if 'halfcredit' in c:
        del c['halfcredit']
    if 'revisions' in c:
        del c['revisions']

    c['departments'] = [Department(abbr=d) for d in c['departments']]
    c['instructors'] = [Instructor(name=x) for x in c['instructors']]
    c['locations'] = [Location(name=l) for l in c.get('locations', [])]
    c['times'] = [TimeSlot(desc=x) for x in c.get('times', [])]
    c['gereqs'] = [GeReq(abbr=x) for x in c.get('gereqs', [])]
    return Course(**c)

# c = s.query(Course).filter(Course.year == '2018').first()
# print(c)

# print(s.query(Course).from_statement(
#     text("SELECT * FROM courses where name LIKE :name")).params(name='%Amer%').all())
