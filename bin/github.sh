#!/bin/bash

# prepare bash
set -ve

# prepare the repositories
git clone --depth=1 https://github.com/StoDevX/course-data.git
cd course-data

git config user.name "Github Databot"
git config user.email "hawkrives+sto-course-databot@gmail.com"

# update course data files

for y in $(seq 1994 $(date +%Y)); do
    for s in $(seq 1 5); do
        echo "$y$s"
    done
done | xargs -t -n1 -P1 -- python3 ../download.py --force-terms -w 1
python3 ../maintain-datafiles.py

if [[ $GITHUB_BRANCH != "master" ]]; then
	git checkout --quiet -b "$GITHUB_BRANCH"
fi

git add .
git commit --quiet -m "course data update $(date)" || (echo "No updates found." && exit 0)
if [[ $GITHUB_BRANCH == "master" ]]; then
	git push origin master -o ci.token=$GH_TOKEN
else
	git push --force origin "$GITHUB_BRANCH" -o ci.token=$GH_TOKEN
fi

# prepare the gh-pages branch
PAGES_BRANCH=gh-pages
if [[ $GITHUB_BRANCH != "master" ]]; then
	PAGES_BRANCH="${GITHUB_BRANCH}-pages"
fi
git checkout --quiet -B "$PAGES_BRANCH" "$GITHUB_BRANCH" --no-track

# update bundled information for public consumption
# python3 ../bundle.py --out-dir ../course-data --format json --format xml --format csv
python3 ../bundle.py --out-dir ../course-data --format json --format xml
python3 ../bundle.py --legacy --out-dir ../course-data/legacy --format json

# remove the source files (quietly)
git rm -rf --quiet details/ raw_xml/

# and … push
if [[ $GITHUB_BRANCH == "master" ]]; then
	git add --all ./
	git commit --quiet -m "course data bundles" --quiet

    git push -f origin gh-pages -o ci.token=$GH_TOKEN
fi
