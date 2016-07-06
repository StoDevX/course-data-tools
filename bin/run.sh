#!/bin/bash

# prepare bash
set -ve

# make sure dependencies are correct
# git pull --rebase origin master
pip3 install --upgrade -r requirements.txt

# prepare the repositories
cd ../
git clone https://github.com/stodevx/course-data.git
cd course-data

# update course data files
python3 ../course-data-tools/download.py --force-terms 2015 2016
python3 ../course-data-tools/maintain-datafiles.py
git add .
git commit -m "update course data for $DATE"
# git push origin master

# update bundled information for public consumption
git branch -d gh-pages
git checkout --orphan gh-pages
python3 ../course-data-tools/bundle.py --format json xml csv

# remove the source files
git rm -rf courses/ details/ raw_xml/
git add .
git commit -m 'course data bundles'
# git push -f origin gh-pages
