#!/bin/bash

# prepare bash
set -ve

# prepare the repositories
git clone --depth=1 https://github.com/stodevx/course-data.git
cd course-data

git config user.name "Heroku Databot"
git config user.email "hawkrives+sto-course-databot@gmail.com"

# update course data files

for y in $(seq 1994 $(date +%Y)); do
    for s in $(seq 1 5); do
        echo "$y$s"
    done
done | xargs -t -n1 -P1 -- python3 ../download.py --force-terms -w 1
python3 ../maintain-datafiles.py

if [[ $TRAVIS_BRANCH != "master" ]]; then
	git checkout -b "$TRAVIS_BRANCH"
fi

git add .
git commit -m "course data update $(date)" || (echo "No updates found." && exit 0)
git push "https://$GITHUB_OAUTH@github.com/stodevx/course-data.git" "$TRAVIS_BRANCH"

# prepare the gh-pages branch
PAGES_BRANCH=gh-pages
if [[ $TRAVIS_BRANCH != "master" ]]; then
	PAGES_BRANCH="${TRAVIS_BRANCH}-pages"
fi
git checkout -B "$PAGES_BRANCH" "$TRAVIS_BRANCH" --no-track

# update bundled information for public consumption
python3 ../bundle.py --out-dir ../course-data --format json --format xml --format csv
python3 ../bundle.py --legacy --out-dir ../course-data/legacy --format json

# remove the source files (quietly)
git rm -rf --quiet details/ raw_xml/

# and … push
if [[ $TRAVIS_BRANCH == "master" ]]; then
	git add --all ./
	git commit -m "course data bundles" --quiet

    git push -f "https://$GITHUB_OAUTH@github.com/stodevx/course-data.git" gh-pages
    curl https://nosnch.in/9243a27544
fi
