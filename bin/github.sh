#!/bin/bash

# prepare bash
set -ve

# update course data files

for y in $(seq 1994 "$(date +%Y)"); do
    for s in $(seq 1 5); do
        course-data-tools download "$y-$s" > "../course-data/raw/$y-$s.xml"
    done
done

course-data-tools maintain-datafiles

if [[ $GITHUB_BRANCH != "master" ]]; then
	git checkout --quiet -b "$GITHUB_BRANCH"
fi

git add .
git commit --quiet -m "course data update $(date)" || (echo "No updates found." && exit 0)

if [[ $GITHUB_BRANCH == "master" ]]; then
	git push origin master
else
	git push --force origin "$GITHUB_BRANCH"
fi

# prepare the gh-pages branch
PAGES_BRANCH=gh-pages
if [[ $GITHUB_BRANCH != "master" ]]; then
	PAGES_BRANCH="${GITHUB_BRANCH}-pages"
fi
git checkout --quiet -B "$PAGES_BRANCH" "$GITHUB_BRANCH" --no-track

# update bundled information for public consumption
course-data-tools bundle --out-dir ../course-data --format json --format xml
course-data-tools bundle --legacy --out-dir ../course-data/legacy --format json

# remove the source files (quietly)
git rm -rf --quiet details/ raw_xml/

# and … push
if [[ $GITHUB_BRANCH == "master" ]]; then
	git add --all ./
	git commit --quiet -m "course data bundles" --quiet

    git push -f origin gh-pages
fi
