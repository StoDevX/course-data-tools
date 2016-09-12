St. Olaf Course Data Tools
==========================

Here lie the tools for extracting course data from the St. Olaf SIS.

There are three scripts: `download.py`, `maintain-datafiles.py`, and `bundle.py`.

All of these tools expect the [course data][course-data] to be one folder up from the CWD, in `../course-data`.

These scripts require `python3` >= 3.4, as well as `beautifulsoup4`, `requests`, `xmltodict`. 

The libraries are also specified in the `requirements.txt` file, so a `pip3 install --user -r requirements.txt` should do it. I *highly* reccommend using [Homebrew](https://brew.sh) to install and update Python on macOS.


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
- `-w, --workers` — how many processes to spawn
- `--format (json|csv|xml)` — how to output the bundle


## `maintain-datafiles.py`
###### Usage: 

```console
./maintain-datafiles.py
```

`maintain-datafiles.py` takes no arguments and does one thing: it loads every course in `../course-data`, and it collects lists of departments, gereqs, instructors, locations, times, and types into `../course-data/data-lists`.


[course-data]: https://github.com/stodevx/course-data
