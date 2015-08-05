#!/bin/bash -vx
# -v = set -o verbose
# -x = set -o xtrace
# -vx prints both

CHANNEL='#integration-cslab'
SLACKBOT_NAME='databot'
SLACKBOT_ICON=':moyai:'
SLACK_URL='https://hooks.slack.com/services/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'

TODAY=$(date)

./scripts/getData.py 2015 --force-download-terms

git add .

git status

git commit -m "[data-update] $TODAY"

git push origin master

curl --silent -X POST --data-urlencode "payload={\"channel\": \"$CHANNEL\", \"username\": \"$SLACKBOT_NAME\", \"text\": \"Data collection completed.\", \"icon_emoji\": \"$SLACKBOT_ICON\"}" $SLACK_URL
