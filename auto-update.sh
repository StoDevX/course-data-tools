#!/bin/bash -v
# -v = set -o verbose

# stop script when command errors
set -e

CHANNEL='#integration-cslab'
SLACKBOT_NAME='databot'
SLACKBOT_ICON=':moyai:'
SLACK_URL='https://hooks.slack.com/services/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'

TODAY=$(date)
YEAR=$(echo 2015 2016)

# update in case code has changed
git pull --rebase origin master
pip3 install --upgrade -r requirements.txt

python3 ./scripts/get-data.py "$YEAR" --force-download-terms

git add .
git status

git commit -m "[data-update] $TODAY"

git push origin master

curl --silent -X POST --data-urlencode "payload={\"channel\": \"$CHANNEL\", \"username\": \"$SLACKBOT_NAME\", \"text\": \"Data collection completed.\", \"icon_emoji\": \"$SLACKBOT_ICON\"}" $SLACK_URL
