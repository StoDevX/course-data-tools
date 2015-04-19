#!/bin/bash

CHANNEL='#gobbldygook-builds'
SLACKBOT_NAME='databot'
SLACKBOT_ICON=':moyai:'
SLACK_URL='https://hooks.slack.com/services/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'

echo "curl POST https://hooks.slack.com"
curl --silent -X POST --data-urlencode "payload={\"channel\": \"$CHANNEL\", \"username\": \"$SLACKBOT_NAME\", \"text\": \"Commencing data collection.\", \"icon_emoji\": \"$SLACKBOT_ICON\"}" $SLACK_URL

echo
echo "./scripts/getData.py 2015 --force-download-terms"

./scripts/getData.py 2015 --force-download-terms

echo
echo "git add ."
git add .

echo
echo "git status"
git status

TODAY=`date`

echo
echo "git commit -m \"[data-update] $TODAY\""
git commit -m "[data-update] $TODAY"

echo
echo "git push origin master"
git push origin master

echo
echo "curl POST https://hooks.slack.com"

curl --silent -X POST --data-urlencode "payload={\"channel\": \"$CHANNEL\", \"username\": \"$SLACKBOT_NAME\", \"text\": \"Data collection completed.\", \"icon_emoji\": \"$SLACKBOT_ICON\"}" $SLACK_URL
