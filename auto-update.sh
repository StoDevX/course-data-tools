#!/bin/bash

./scripts/getData.py 20151 20152 20153 --force-download-terms

git add .
git status

TODAY=`date`

git commit -m "[data-update] $TODAY"
git push origin master

