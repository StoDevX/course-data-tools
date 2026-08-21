from sqlite_utils import Database

from bundle import build_database, resolve_terms


def course(clbid, **overrides):
    c = {
        'clbid': clbid,
        'crsid': '0000000747',
        'term': 20233,
        'year': 2023,
        'semester': 3,
        'department': 'MATH',
        'number': 252,
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


def test_build_database_writes_every_course(tmp_path):
    path = tmp_path / 'catalog.db'
    build_database(path, [course('0000000001'), course('0000000002')])
    assert len(list(Database(path)['section'].rows)) == 2


def test_build_database_replaces_an_existing_file(tmp_path):
    """A full rebuild must not inherit rows from the previous run."""
    path = tmp_path / 'catalog.db'
    build_database(path, [course('0000000001')])
    build_database(path, [course('0000000002')])
    assert [r['clbid'] for r in Database(path)['section'].rows] == [2]


def test_build_database_accepts_a_generator(tmp_path):
    """run() streams courses lazily rather than materializing every term."""
    path = tmp_path / 'catalog.db'
    build_database(path, (course(f'000000000{n}') for n in (1, 2, 3)))
    assert len(list(Database(path)['section'].rows)) == 3


def test_resolved_terms_survive_a_second_walk():
    """calculate_terms yields a generator; the sqlite pass walks terms again."""
    terms = resolve_terms([20233])
    assert list(terms) == [20233]
    assert list(terms) == [20233]
