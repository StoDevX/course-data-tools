#!/bin/bash

# prepare bash
set -ve

# prepare the repositories
if [ ! -d ./course-data ]; then
	git clone -q https://github.com/stodevx/course-data.git
fi
cd course-data

git checkout master
git pull origin master

git config user.name "Heroku Databot"
git config user.email "hawkrives+sto-course-databot@gmail.com"

# update course data files
python3 ../download.py --force-terms 2015 2016 -w 2
python3 ../maintain-datafiles.py

git add .
git commit -m "course data update $(date)" || (echo "No updates found." && exit 0)
git push "https://$GITHUB_OAUTH@github.com/stodevx/course-data.git" master

# prepare the gh-pages branch
if test "$(git branch --list gh-pages)"; then
	git branch -D gh-pages
fi
git checkout -B gh-pages master --no-track

# update bundled information for public consumption
python3 ../bundle.py --out-dir ../course-data --format json --format xml --format csv
python3 ../bundle.py --legacy --out-dir ../course-data/legacy --format json

# remove the source files (quietly)
git rm -rf --quiet courses/ details/ raw_xml/

# and … push
git add --all ./
git commit -m "course data bundles" --quiet
git push -f "https://$GITHUB_OAUTH@github.com/stodevx/course-data.git" gh-pages
