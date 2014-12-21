Gobbldygook Course Data
=======================

**Date Last Updated:** Dec. 8, 2014

This repository holds the data for Gobbldygook in both raw (XML) and proccessed (JSON) forms. You do not need this repository if your are only interested in using Gobbldygook; it includes this as a submodule.



To Update the Data
------------------

Use Github!

1. Fork this repository
2. Make a branch titled `data-year-month-day`, where year, month, and day become the year, month, and day, respectively
3. Run `make update`
4. Submit a pull request against my `master` branch



What changes?
-------------

- Unescape `&amp;` in `coursename` (also remap to `name`)
- Map `coursesection` to `sect`
- Remove `<br>` tags from `notes`
- Remove `coursestatus`
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
- Map `meetinglocations` to `places`
- Map `meetingtimes` to `times`
- Map `instructors` to `profs`
  - `profs` change to "First Last", instead of "Last, First" (and become a list)
- Get the GE Reqs as a list (and without the links)
- Same with `places`
- Change `times` to a list



Notes
-----

Package versioning: I'm trying to use semver. Therefore:

- the first number is incremented for non-backwards-compatible changes to the package format,
- the second number is incremented for other stuff,
- the third number is the date on which the data was updated,
- and the fourth number is incremented when:
    - you need to push multiple versions on the same day
    - you are playing around with something in getData
    - etc.

Examples: `2.1.2014-11-30.0`


getData.py
----------

Before using this script, you'll need a some other libraries:

- Python 3.4 or greater (3.3 and below might work, but I don't test on them.)
- `beautifulsoup4`
- `requests`
- `xmltodict`

so a `pip3 install beautifulsoup4 requests xmltodict` should do it.

As an additional note, I *highly* reccommend using [Homebrew](http://brew.sh) to install/update Python.


### Usage

`python3 getData.py --years 1994 1995 --terms 20141`

Simply calling `python3 getData.py` will run it on every term from 19941 to the current year.

- `--years`: Update all applicable terms for the given years.
- `--terms`: Only update the given terms.
- `--force`, `-f`: Force it to update from the server – not ideal, generally, and only to be used when the data needs to be updated.
- `--dry-run`, `-d`: Don't modify any files on disk.
- `--quiet`, `-q`: Run quietly.
- `--output-type`: Defaults to `json`. Acceptable values: `json`, `csv`.
