#!/bin/bash

# prepare bash
set -ve

# prepare the repositories
git clone https://github.com/stodevx/course-data.git
git clone https://github.com/stodevx/course-data-tools.git
cd course-data

# update course data files
python3 ../course-data-tools/download.py "$YEARS"
python3 ../course-data-tools/maintain-datafiles.py "$YEARS"
git add .
git commit -m "update course data for $DATE"
git push origin master

# update bundled information for public consumption
git branch -d gh-pages
git checkout --orphan gh-pages
python3 ../course-data-tools/bundle.py --out ./ --format json xml csv

# remove the source files
git rm -rf courses/ details/ raw_xml/
git add .
git commit -m 'course data bundles'
git push -f origin gh-pages
