#!/bin/bash -v
# -v = set -o verbose

# stop script when command errors
set -e 

CHANNEL='#integration-cslab'
SLACKBOT_NAME='databot'
SLACKBOT_ICON=':moyai:'
SLACK_URL='https://hooks.slack.com/services/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'

TODAY=$(date)
YEAR=$(date +%Y)

./scripts/get-data.py "$YEAR" --force-download-terms

git add .
git status

git commit -m "[data-update] $TODAY"

git pull --rebase origin master 
git push origin master

curl --silent -X POST --data-urlencode "payload={\"channel\": \"$CHANNEL\", \"username\": \"$SLACKBOT_NAME\", \"text\": \"Data collection completed.\", \"icon_emoji\": \"$SLACKBOT_ICON\"}" $SLACK_URL

