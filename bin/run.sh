#!/bin/bash

# prepare bash
set -ve

# prepare the repositories
cd ../
if [ ! -d ./course-data ]; then
	git clone https://github.com/stodevx/course-data.git
fi
cd course-data
git checkout master

# update course data files
python3 ../course-data-tools/download.py --force-terms 2015 2016
python3 ../course-data-tools/maintain-datafiles.py
git add .
git commit -m "course data update $(date)" || (echo "No updates found." && exit 0)
git push origin master

# update bundled information for public consumption
git checkout gh-pages
git merge -m "merge course data" master
python3 ../course-data-tools/bundle.py --format json xml csv

# remove the source files
git add .
git commit -m 'course data bundles'
git push -f origin gh-pages

curl https://nosnch.in/9243a27544
