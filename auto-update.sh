#!/bin/bash

curl -X POST --data-urlencode 'payload={"channel": "#gobbldygook-builds", "username": "databot", "text": "Beginning data collection.", "icon_emoji": ":ghost:"}' https://hooks.slack.com/services/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

./scripts/getData.py 20151 20152 20153 --force-download-terms

git add .
git status

TODAY=`date`

git commit -m "[data-update] $TODAY"
git push origin master

curl -X POST --data-urlencode 'payload={"channel": "#gobbldygook-builds", "username": "databot", "text": "Data collection completed.", "icon_emoji": ":ghost:"}' https://hooks.slack.com/services/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