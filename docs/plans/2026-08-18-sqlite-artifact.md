# SQLite Artifact Pipeline Implementation Plan

> **For Claude:** Use `skills/collaboration/executing-plans` to implement this plan task-by-task.

**Goal:** Build a normalized SQLite database of St. Olaf course data on every nightly run and publish it as a GitHub Release asset on `StoDevX/course-data`, so other applications can consume it directly.

**Architecture:** The JSON course files in `../course-data/courses/` remain the source of truth. The database is a *derived view*, rebuilt from scratch on every run — no incremental upsert, no drift. The build is a serial pass in the parent process after the parallel per-term format passes finish, which sidesteps the concurrent-writer problem in the current code. `sqlite` becomes a `--format` choice alongside `json|csv|xml`, so it is opt-in and existing behavior is unchanged.

**Tech Stack:** Python 3.13, uv, sqlite-utils 4.2.1, pytest, GitHub Actions, `gh release upload`.

**Branch:** Work continues on the existing `sqlite-utils` branch. No worktree — the branch is already scoped to exactly this work.

---

## Context for the implementer

Read this before starting. You will not guess these from the code.

### How the pipeline fits together

There are three entry points, all expecting the course data repo checked out at `../course-data`:

1. `download.py` — fetches XML from the SIS, converts each course to a JSON file at
   `../course-data/courses/<thousands>/<clbid>.json`, and writes a per-term index of
   clbids to `../course-data/courses/_index/<term>.json`.
2. `maintain-datafiles.py` — builds lists of departments/gereqs/instructors into `data-lists/`.
3. `bundle.py` — reads the per-term indexes, loads those course JSON files, and writes
   bundles to `../course-data/terms/<term>.<ext>`.

`bin/github.sh` runs all three in CI, commits the JSON to `master`, then rebuilds bundles on a
force-pushed `gh-pages` branch.

### Known shape of the data

Surveyed from a random sample of 3,000 of the 71,910 files in `../course-data/courses/`:

| Key | Present | Notes |
|---|---|---|
| `clbid`, `crsid`, `credits`, `instructors`, `level`, `name`, `semester`, `status`, `term`, `type`, `year` | 100% | always safe to index directly |
| `number`, `pn` | 99.7% | missing only on 8 legacy list-shaped files |
| `department`, `enrolled`, `max` | 97.4% | **must use `.get()`** |
| `learningmode` | 95.3% | **must use `.get()`**; see Task 3 |
| `offerings` | 61% | list of `{day, start, end, location}` |
| `description` | 48% | **a list of strings**, not a string |
| `section`, `title`, `gereqs`, `notes` | 20–46% | `notes` is **plural** in the JSON |
| `firstyear`, `sophomore`, `junior`, `senior` | ~8–10% | strings like `"0/0"`, not ints |

Value domains: `status` is `O`/`C`/`X`. `semester` is `1`–`5`. `type` is one of
Research/Lab/Topic/Seminar/FLAC/Discussion/Ensemble. `learningmode` is `""`/`A`/`S`.

Eight files under `../course-data/courses/` are JSON *lists*, not objects — legacy junk.
They are not referenced by any `_index/<term>.json`, so `load_some_courses` never yields them.
Do not add handling for them.

### Bugs being fixed along the way

These are pre-existing and in scope because the migration or the schema work trips over them:

- `lib/process_courses.py:121` — `course['pn'] is 'Y'` is an identity comparison on a string
  literal. It happens to work via CPython interning, but on Python 3.13 it raises
  `SyntaxWarning: "is" with 'str' literal`. Must become `==` for the version bump to be clean.
- `lib/database.py:8` — reads `course.get("note", [])`; the JSON key is `notes`. Always empty today.
- `lib/database.py:14` — reads `course["learningmode"]`; raises `KeyError` on ~5% of courses.
- `lib/database.py` `pass_nopass` — derived by searching the description for
  `"Pass or No Pass (P/N) only"`, which matches 10 courses in the sample, while the real `pn`
  boolean is true for 500. Use `pn`.
- `bundle.py:40` — `generate_sqlite_db` is called inside the `for f in args.format` loop, so it
  runs once per requested format.
- `bundle.py:44` — opens `Database("catalog.db")` per term while `run()` fans out across
  `ProcessPoolExecutor(max_workers=cpu_count())`. N processes writing one SQLite file.
- `bundle.py:39` — `save_term` is commented out, so JSON/CSV/XML output is currently dead.

### Target schema

```
section(clbid PK, crsid, term, year, semester, department, number, section,
        level, type, name, title, description, credits, pass_nopass,
        learning_mode, status, enrolled, max,
        firstyear, sophomore, junior, senior, notes)

offering(id PK, clbid FK -> section.clbid, day, start, end, location)

instructor(id PK, name UNIQUE)
section_instructor(clbid FK, instructor_id FK)

gereq(id PK, code UNIQUE)
section_gereq(clbid FK, gereq_id FK)
```

`description` and `notes` are lists in the JSON; join them with `\n` into a single column.
Instructors and gereqs get **one row per name/code** — the current code joins them with `,`
into a single row, which is the thing we are fixing.

---

## Task 1: Repo hygiene

**Files:**
- Modify: `.gitignore`
- Delete: `Pipfile`

**Step 1: Add the build artifacts to `.gitignore`**

Append to `.gitignore`:

```
*.sqlite
*.sqlite3
*.db
```

**Step 2: Delete the stale Pipfile**

```bash
rm Pipfile
```

It pins `requests==2.32.0` and `python_version = "3.9"`, contradicting `requirements.txt`
(`2.32.4`) and the workflows (`3.8`). It is being replaced by `pyproject.toml` in Task 2.

**Step 3: Verify nothing untracked remains**

Run: `git status --short`
Expected: clean except the `.gitignore` modification.

**Step 4: Commit**

```bash
git add .gitignore Pipfile
git commit -m "ignore local database artifacts; drop stale Pipfile"
```

---

## Task 2: Migrate to uv and Python 3.13

**Files:**
- Create: `pyproject.toml`, `uv.lock`
- Delete: `requirements.txt`
- Modify: `.github/workflows/check.yml`, `.github/workflows/update-data.yml`, `bin/github.sh`, `bin/run.sh`, `README.md`

**Step 1: Write `pyproject.toml`**

```toml
[project]
name = "course-data-tools"
version = "0.1.0"
description = "Tools for extracting course data from the St. Olaf SIS"
requires-python = ">=3.13"
dependencies = [
    "beautifulsoup4>=4.12",
    "requests>=2.32.4",
    "xmltodict>=0.13",
    "sqlite-utils>=4.2.1",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pylint>=3.3",
]

[tool.pytest.ini_options]
testpaths = ["lib", "."]
python_files = ["test_*.py"]
```

`pytest` and `pylint` move to a dev group — they are not runtime dependencies and CI only
needs them for the check job.

**Step 2: Lock and sync**

```bash
uv lock
uv sync
```

Expected: creates `uv.lock` and `.venv/`. Note `venv/` is already gitignored but `.venv/` is
not — add `.venv/` to `.gitignore` if `git status` shows it.

**Step 3: Verify the existing tests still pass on 3.13**

```bash
uv run pytest lib/ -v
```

Expected: `lib/test_calculate_terms.py` and `lib/test_parse_timestring.py` pass.
If `test_calculate_terms` fails on date arithmetic, that is a real pre-existing failure —
report it, do not paper over it.

**Step 4: Fix the `is 'Y'` SyntaxWarning**

This blocks 3.13. In `lib/process_courses.py:121`:

```python
    # Turn booleans into booleans
    course['pn'] = True if course['pn'] == 'Y' else False
```

Verify no warnings remain:

```bash
uv run python -W error::SyntaxWarning -c "import lib.process_courses"
```
Expected: no output, exit 0.

**Step 5: Update `.github/workflows/check.yml`**

Replace the `setup-python` + `pip install` steps with:

```yaml
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true
      - name: Install dependencies
        run: uv sync --all-groups
      - name: Run tests
        run: uv run pytest lib/ -v
```

Drop the `strategy.matrix.python-version` block — `requires-python` in `pyproject.toml` now
governs, and `uv` provisions the interpreter itself.

Note: the current check job installs dependencies and then does nothing with them — it never
runs pytest or pylint despite being named "Check dependencies". Adding the test step is the fix.

**Step 6: Update `.github/workflows/update-data.yml`**

Same substitution: drop `setup-python` and the matrix, add `astral-sh/setup-uv@v5` and
`uv sync`. Leave the `push-on-course-data-change` step and its env block alone.

**Step 7: Update the shell scripts**

In `bin/github.sh` and `bin/run.sh`, change every `python3 ../download.py`,
`python3 ../maintain-datafiles.py`, and `python3 ../bundle.py` invocation to `uv run --project .. ../<script>`.

The `--project ..` is required because both scripts `cd course-data` before invoking the tools.

**Step 8: Update `README.md`**

Replace:

> These scripts require `python3` >= 3.8, as well as `beautifulsoup4`, `requests`, `xmltodict`, `sqlite-utils`.
>
> The libraries are also specified in the `Pipfile` file, so a `pip3 install pipenv` and `pipenv run $command`

with:

> These scripts require `python3` >= 3.13 and [uv](https://docs.astral.sh/uv/).
>
> Run `uv sync` once, then invoke the tools with `uv run ./download.py` and friends.

**Step 9: Commit**

```bash
git add pyproject.toml uv.lock .gitignore .github/workflows bin README.md lib/process_courses.py
git rm requirements.txt
git commit -m "migrate to uv and python 3.13"
```

---

## Task 3: Add `learningmode` default (issue #8)

`learningmode` already reaches the JSON for ~95% of courses. The gap is that an empty
`<learningmode></learningmode>` — which means "All Learning Modes" and is a *meaningful* value
per the issue — parses to `None` and is then stripped by the final dict comprehension in
`clean_course`. Pre-2020 terms have no tag at all.

**Files:**
- Test: `lib/test_process_courses.py` (create)
- Modify: `lib/process_courses.py`

**Step 1: Write the failing tests**

Create `lib/test_process_courses.py`:

```python
from .process_courses import clean_course


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
        'instructors': None,
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
```

**Step 2: Run to verify they fail**

Run: `uv run pytest lib/test_process_courses.py -v`
Expected: the two empty/missing tests FAIL with `KeyError: 'learningmode'`.

**Step 3: Implement**

In `clean_course`, immediately before the final `return` comprehension:

```python
    # An absent learningmode means "All Learning Modes"; preserve it as a
    # value rather than letting the None-stripping comprehension drop it.
    course['learningmode'] = course.get('learningmode') or ''
```

**Step 4: Run to verify they pass**

Run: `uv run pytest lib/test_process_courses.py -v`
Expected: 4 passed.

**Step 5: Commit**

```bash
git add lib/process_courses.py lib/test_process_courses.py
git commit -m "always emit learningmode in course json

Closes StoDevX/course-data#8"
```

---

## Task 4: Rewrite `lib/database.py` against the normalized schema

Drew explicitly approved this rewrite.

**Files:**
- Modify: `lib/database.py` (full rewrite)
- Test: `lib/test_database.py` (create)

**Step 1: Write the failing tests**

Create `lib/test_database.py`:

```python
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
```

**Step 2: Run to verify they fail**

Run: `uv run pytest lib/test_database.py -v`
Expected: all FAIL with `ImportError: cannot import name 'create_schema'`.

**Step 3: Implement `lib/database.py`**

Replace the entire file:

```python
"""Write course data into a normalized SQLite catalog.

The JSON course files are the source of truth; this database is a derived view
that is rebuilt from scratch on every run.
"""


def create_schema(db):
    """Create the catalog tables and their indexes if they do not yet exist."""
    db["section"].create({
        "clbid": int,
        "crsid": int,
        "term": int,
        "year": int,
        "semester": int,
        "department": str,
        "number": str,
        "section": str,
        "level": int,
        "type": str,
        "name": str,
        "title": str,
        "description": str,
        "credits": float,
        "pass_nopass": int,
        "learning_mode": str,
        "status": str,
        "enrolled": int,
        "max": int,
        "firstyear": str,
        "sophomore": str,
        "junior": str,
        "senior": str,
        "notes": str,
    }, pk="clbid", if_not_exists=True)

    db["instructor"].create({
        "id": int,
        "name": str,
    }, pk="id", if_not_exists=True)
    db["instructor"].create_index(["name"], unique=True, if_not_exists=True)

    db["gereq"].create({
        "id": int,
        "code": str,
    }, pk="id", if_not_exists=True)
    db["gereq"].create_index(["code"], unique=True, if_not_exists=True)

    db["offering"].create({
        "id": int,
        "clbid": int,
        "day": str,
        "start": str,
        "end": str,
        "location": str,
    }, pk="id", foreign_keys=[("clbid", "section", "clbid")], if_not_exists=True)
    db["offering"].create_index(["clbid"], if_not_exists=True)

    db["section_instructor"].create({
        "clbid": int,
        "instructor_id": int,
    }, pk=("clbid", "instructor_id"), foreign_keys=[
        ("clbid", "section", "clbid"),
        ("instructor_id", "instructor", "id"),
    ], if_not_exists=True)

    db["section_gereq"].create({
        "clbid": int,
        "gereq_id": int,
    }, pk=("clbid", "gereq_id"), foreign_keys=[
        ("clbid", "section", "clbid"),
        ("gereq_id", "gereq", "id"),
    ], if_not_exists=True)


def join_paragraphs(value):
    """Course descriptions and notes are lists of strings in the JSON."""
    return "\n".join(value) if value else ""


def build_section(course):
    return {
        "clbid": int(course["clbid"]),
        "crsid": int(course["crsid"]),
        "term": int(course["term"]),
        "year": int(course["year"]),
        "semester": int(course["semester"]),
        "department": course.get("department"),
        "number": str(course.get("number", "")),
        "section": course.get("section"),
        "level": course.get("level"),
        "type": course.get("type"),
        "name": course.get("name"),
        "title": course.get("title"),
        "description": join_paragraphs(course.get("description")),
        "credits": course.get("credits"),
        "pass_nopass": 1 if course.get("pn") else 0,
        "learning_mode": course.get("learningmode") or "",
        "status": course.get("status"),
        "enrolled": course.get("enrolled"),
        "max": course.get("max"),
        "firstyear": course.get("firstyear"),
        "sophomore": course.get("sophomore"),
        "junior": course.get("junior"),
        "senior": course.get("senior"),
        "notes": join_paragraphs(course.get("notes")),
    }


def build_offering(clbid, offering):
    return {
        "clbid": clbid,
        "day": offering["day"],
        "start": offering["start"],
        "end": offering["end"],
        "location": offering["location"],
    }


def link(db, table, lookup, clbid, join_table, join_column):
    """Resolve a shared lookup row, then link it to this section."""
    for value in lookup:
        row_id = db[table].lookup({table_key(table): value})
        db[join_table].insert(
            {"clbid": clbid, join_column: row_id},
            replace=True,
        )


def table_key(table):
    return "code" if table == "gereq" else "name"


def insert_course(db, course):
    clbid = int(course["clbid"])

    db["section"].insert(build_section(course), pk="clbid", replace=True)

    # A rebuild must not accumulate stale rows for a section.
    db["offering"].delete_where("clbid = ?", [clbid])
    offerings = [build_offering(clbid, o) for o in course.get("offerings") or []]
    if offerings:
        db["offering"].insert_all(offerings)

    db["section_instructor"].delete_where("clbid = ?", [clbid])
    link(db, "instructor", course.get("instructors") or [], clbid,
         "section_instructor", "instructor_id")

    db["section_gereq"].delete_where("clbid = ?", [clbid])
    link(db, "gereq", course.get("gereqs") or [], clbid,
         "section_gereq", "gereq_id")


def tracer(sql, params):
    print(f'SQL: {sql} - params: {params}')
```

**Step 4: Run to verify they pass**

Run: `uv run pytest lib/test_database.py -v`
Expected: 11 passed.

If `Table.lookup()` or `if_not_exists=` behave differently in sqlite-utils 4.2.1 than assumed,
consult `uv run python -c "import sqlite_utils.db, inspect; print(inspect.signature(sqlite_utils.db.Table.lookup))"`
and adjust — do not weaken the tests to match.

**Step 5: Commit**

```bash
git add lib/database.py lib/test_database.py
git commit -m "normalize the sqlite catalog schema

Sections are keyed on clbid so rebuilds are idempotent. Instructors and
gereqs become shared lookup rows joined many-to-many rather than a single
comma-joined string. Offerings become a plain one-to-many table."
```

---

## Task 5: Wire `sqlite` into `bundle.py` as a format

**Files:**
- Modify: `bundle.py`
- Test: `test_bundle.py` (create, at repo root)

**Step 1: Write the failing test**

Create `test_bundle.py`:

```python
from sqlite_utils import Database

from bundle import build_database


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
```

**Step 2: Run to verify it fails**

Run: `uv run pytest test_bundle.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_database'`.

**Step 3: Implement**

In `bundle.py`, restore `save_term` in `one_term` and drop the DB call from the worker:

```python
def one_term(args, term):
    pretty_term = f'{str(term)[:4]}:{str(term)[4]}'

    log(pretty_term, 'Loading courses')
    courses = list(load_some_courses(term))

    if args.legacy:
        [regress_course(c) for c in courses]

    log(pretty_term, 'Saving term')
    for f in args.format:
        if f == 'sqlite':
            continue  # built serially after the parallel passes; see run()
        save_term(term, courses, kind=f, root_path=args.out_dir)
```

Add the serial builder. It replaces any existing file, because the database is a derived view
rebuilt from scratch:

```python
def build_database(path, courses, should_trace=False):
    """Rebuild the catalog from scratch at `path`."""
    if os.path.exists(path):
        os.remove(path)

    db = Database(path, tracer=tracer if should_trace else None)
    create_schema(db)
    with db.conn:
        for course in courses:
            insert_course(db, course)
    return db
```

Then in `run()`, after the parallel map and before `json_folder_map`:

```python
    if 'sqlite' in args.format:
        log('sqlite', 'Building catalog')
        path = os.path.join(args.out_dir, 'catalog.db')
        courses = (c for term in terms for c in load_some_courses(term))
        build_database(path, courses, should_trace=args.trace)
```

Note `terms` must be a `list`, not a generator, since it is consumed twice — check that
`list_all_course_index_files()` result is wrapped in `list()` (it already is at `bundle.py:57`).

Update imports at the top of `bundle.py`:

```python
from lib.database import create_schema, insert_course, tracer
from lib.save_term import save_term
```

Add `sqlite` to the `--format` choices:

```python
    argparser.add_argument('--format',
                           action='append',
                           nargs='?',
                           choices=['json', 'csv', 'xml', 'sqlite'],
                           help='Change the output filetype')
```

**Step 4: Run to verify it passes**

Run: `uv run pytest test_bundle.py -v`
Expected: 2 passed.

**Step 5: Verify against real data**

```bash
uv run ./bundle.py 20233 --format sqlite --out-dir /tmp/bundle-check
uv run sqlite-utils tables /tmp/bundle-check/catalog.db --counts
uv run sqlite-utils /tmp/bundle-check/catalog.db \
  "select clbid, name, learning_mode, credits from section limit 5" --table
```

Expected: six tables with non-zero counts; `learning_mode` populated. `20233` is the only term
with raw XML checked out locally, so it is the reliable one to smoke-test.

Run it **twice** and confirm the row counts are identical — that is the idempotence check.

**Step 6: Commit**

```bash
git add bundle.py test_bundle.py
git commit -m "add sqlite as a bundle format

The database is built in a single serial pass after the parallel per-term
format passes, rather than from inside each worker process — concurrent
writers to one sqlite file was the bug."
```

---

## Task 6: Publish the database as a release asset

**Files:**
- Modify: `bin/github.sh`, `.github/workflows/update-data.yml`
- Modify: `README.md`

**Step 1: Build the database alongside the other bundles**

In `bin/github.sh`, add `--format sqlite` to the main bundle invocation:

```bash
uv run --project .. ../bundle.py --out-dir ../course-data --format json --format xml --format csv --format sqlite
```

Leave the `--legacy` invocation alone — the legacy gobbldygook format has no database analogue.

**Step 2: Keep the binary out of the gh-pages commit**

`bin/github.sh` runs `git add --all ./` on the gh-pages branch, which would sweep `catalog.db`
into a force-pushed branch. Immediately before that `git add`, move it out:

```bash
# The catalog is published as a release asset, not committed to gh-pages.
mv catalog.db "$GITHUB_WORKSPACE/catalog.db"
```

**Step 3: Upload the asset**

Add a step to `.github/workflows/update-data.yml`, after `push-on-course-data-change`:

```yaml
      - name: publish-course-catalog
        if: github.ref_name == 'master'
        run: |
          gh release create catalog \
            --repo StoDevX/course-data \
            --title "Course catalog database" \
            --notes "Rolling SQLite build of the St. Olaf course catalog. Rebuilt nightly." \
            || true
          gh release upload catalog "$GITHUB_WORKSPACE/catalog.db" \
            --repo StoDevX/course-data --clobber
        env:
          GH_TOKEN: ${{ secrets.COURSE_DATA_TOOLS_GH_PUSH_TOKEN }}
```

The `|| true` on `release create` makes the step idempotent — it fails harmlessly once the
`catalog` tag exists. `--clobber` replaces the asset in place, so the download URL is stable:

```
https://github.com/StoDevX/course-data/releases/download/catalog/catalog.db
```

The `if:` guard mirrors the existing branch conditionals in `bin/github.sh`, which only push to
`gh-pages` from `master`.

**Step 4: Document the artifact in `README.md`**

Add a section under `bundle.py`:

```markdown
###### Output:

`--format sqlite` writes `catalog.db` into `--out-dir`. The nightly workflow publishes it to
<https://github.com/StoDevX/course-data/releases/download/catalog/catalog.db>, which is a
stable URL that always serves the most recent build.
```

Add `sqlite` to the documented `--format` argument list.

**Step 5: Verify the workflow parses**

```bash
uv run python -c "import yaml,sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]" \
  .github/workflows/update-data.yml .github/workflows/check.yml
```
Expected: no output, exit 0. (`uv run --with pyyaml` if pyyaml is not in the lock.)

**Step 6: Commit**

```bash
git add bin/github.sh .github/workflows/update-data.yml README.md
git commit -m "publish the course catalog database as a release asset"
```

---

## Verification before opening a PR

```bash
uv run pytest -v                     # all tests, including the two pre-existing ones
uv run pylint lib/ bundle.py download.py --errors-only
uv run ./bundle.py 20233 --format json --format sqlite --out-dir /tmp/verify
```

Confirm `/tmp/verify/terms/20233.json` and `/tmp/verify/catalog.db` both exist — JSON output
must still work, since restoring it is half of Task 5.

**Not in scope, worth filing separately:**

- `bin/github.sh` re-downloads every term from 1994 nightly. That is slow and hammers the SIS.
- `download.py` has a four-deep nested `try/except` retry ladder in
  `lib/fetch_term_data.py:load_data_from_server` that should be a loop.
- The eight list-shaped JSON files under `../course-data/courses/` are unreachable legacy data.
