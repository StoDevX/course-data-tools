#!/bin/bash

# prepare bash
set -ve

# prepare the repositories
git clone --depth=1 https://github.com/stodevx/course-data.git
cd course-data

git config user.name "Heroku Databot"
git config user.email "hawkrives+sto-course-databot@gmail.com"

# update course data files

python3 ../download.py --force-terms -w 1
python3 ../maintain-datafiles.py

git add .
git commit -m "course data update $(date)" || (echo "No updates found." && exit 0)
git push "https://$GITHUB_OAUTH@github.com/stodevx/course-data.git" master

# prepare the gh-pages branch
git checkout -B gh-pages master --no-track

# update bundled information for public consumption
python3 ../bundle.py --out-dir ../course-data --format json --format xml --format csv
python3 ../bundle.py --legacy --out-dir ../course-data/legacy --format json

# remove the source files (quietly)
git rm -rf --quiet details/ raw_xml/

# and … push
git add --all ./
git commit -m "course data bundles" --quiet
git push -f "https://$GITHUB_OAUTH@github.com/stodevx/course-data.git" gh-pages

curl https://nosnch.in/9243a27544
