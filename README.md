Gobbldygook Course Data
=======================

This repository holds the data for Gobbldygook in both raw (XML) and proccessed (JSON) forms. You do not need this repository if your are only interested in using Gobbldygook.


## Usage
`./scripts/getData.py --years 1994 1995 --terms 20141`

Simply calling `getData.py` will run it on every term from 19941 to the current year.

- `--years`: Update all applicable terms for the given years.
- `--terms`: Only update the given terms.
- `--force-update-terms`, `-f`: Force it to update terms from the server – not ideal, generally, and only to be used when the data needs to be updated.
- `--dry-run`, `-d`: Don't modify any files on disk.
- `--quiet`, `-q`: Run quietly.
- `--output-type`: Defaults to `json`. Acceptable values: `json`, `csv`.
- `--output-dir`: The folder to spit terms into. Defaults to `build/`.


## getData.py

Before using this script, you'll need some other things:

- Python 3.3 or greater
- `beautifulsoup4`
- `requests`
- `xmltodict`

The libraries are also specified in `requirements.txt`, so a `pip3 install --user -r requirements.txt` should do it.

As an additional note, I *highly* reccommend using [Homebrew](http://brew.sh) to install/update Python.


## What changes?

- Unescape `&amp;` in `coursename` (also remap to `name`)
- Map `coursesection` to `section`
- Remove `<br>` tags from `notes`
- Remove `varcredits`
    – no idea what it does; it's been "N" for every single course in the database
- Expand `courseubtype` and map to `type`
    - f. ex., `R` becomes `Research`
- Departments becomes a list
- Turn the *really long number strings* into actual numbers
    - `clbid` becomes an int
    - `coursenumber` maps to `num` and becomes an int
    - `credits` becomes a float
    - `crsid` becomes an int
    - `groupid` becomes an int
- Turn fake-booleans into booleans
  - namely `pn` maps to `pf` and becomes `True` or `False`, instead of `'Y'` or `'N'`.
- Embed the term, year, and semester
- Embed the course level (first digit of the number)
- Map `meetinglocations` to `locations`
- Map `meetingtimes` to `times`
- Change `instructors` to "First Last", instead of "Last, First" (and become a list)
- Get the GE Reqs as a list (and without the links)
- Same with `locations`
- Change `times` to a list
