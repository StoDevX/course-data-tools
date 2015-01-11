#!/bin/sh

git pull --rebase

for path in courses related-data; do
	cd "$path"

	pwd

	echo ""
	node ../scripts/version.js
	echo ""

	read -p "New Version [major|minor|patch]: " version
	npm version $version

	npm publish

	cd ../
done

git push --follow-tags
