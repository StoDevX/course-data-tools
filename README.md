# St. Olaf Course Data Tools

Here lie the tools for extracting course data from the St. Olaf SIS.

There are three scripts: `download.py`, `maintain-datafiles.py`, and `bundle.py`.

All of these tools expect the [course data][course-data] to be one folder up from the CWD, in `../course-data`.

These scripts require `python3` >= 3.13 and [uv][uv].

Run `uv sync` once, then invoke the tools with `uv run ./download.py` and friends.

## `download.py`

###### Usage:

```console
./download.py
./download.py 2016
./download.py 1994 1995 20141
```

You can pass a mix of years and terms to `download.py`. A term is a year followed by `1-5` – 1 for fall, 5 for summer session 2.

###### Arguments:

- `-w, --workers` — how many processes to spawn
- `--force-terms` — force downloading the terms from the SIS
- `--force-details` — force downloading the course details from the SIS
- `--no-revisions` — don't check for revisions
- `--ignore-revisions $PROP` — don't check for revisions in these properties
- `-q, --quiet` — be quieter

## `bundle.py`

###### Usage:

```console
./bundle.py
./bundle.py 2016
./bundle.py 1994 1995 20141
```

You can pass a mix of years and terms to `bundle.py`. A term is a year followed by `1-5` – 1 for fall, 5 for summer session 2.

`bundle.py` outputs bundles into `../course-data/terms`.

###### Arguments:

- `-w` — how many processes to spawn
- `--format (json|csv|xml|sqlite)` — how to output the bundle. can be given multiple times to generate multiple formats
- `--legacy` — create files in the legacy gobbldygook format
- `--out-dir` — path to a folder to contain the output
- `--trace` — print every sqlite query as it runs

###### The course catalog database:

`--format sqlite` writes a normalized `catalog.db` into `--out-dir`. Unlike the per-term
bundles it covers every requested term in one file, and it is rebuilt from scratch on each
run — the JSON course files remain the source of truth.

```
section(clbid PK, crsid, term, year, semester, department, number, section,
        level, type, name, title, description, credits, pass_nopass,
        learning_mode, status, enrolled, enrollment_max, enrollment_fy,
        enrollment_so, enrollment_jr, enrollment_sr, notes)
offering(id PK, clbid → section, day, start, end, location)
instructor(id PK, name)  ⟷  section_instructor(clbid, instructor_id)
gereq(id PK, code)       ⟷  section_gereq(clbid, gereq_id)
```

The nightly workflow commits it to the `gh-pages` branch alongside the other bundles, so
these URLs always serve the most recent build:

<https://raw.githubusercontent.com/StoDevX/course-data/gh-pages/catalog.db>

<http://stolaf.dev/course-data/catalog.db>

## `maintain-datafiles.py`

###### Usage:

```console
./maintain-datafiles.py
```

`maintain-datafiles.py` takes no arguments and does one thing: it loads every course in `../course-data`, and it collects lists of departments, gereqs, instructors, locations, times, and types into `../course-data/data-lists`.

[course-data]: https://github.com/stodevx/course-data
[uv]: https://docs.astral.sh/uv/
