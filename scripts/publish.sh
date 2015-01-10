#!/bin/sh

git pull --rebase

echo ""
node ./scripts/version.js
echo ""

read -p "New Version [major|minor|patch]: " version
npm version $version

npm publish

git push --follow-tags
