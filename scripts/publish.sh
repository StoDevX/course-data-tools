#!/bin/sh

git pull --rebase

for path in build related-data; do
	cd "$path"

	pwd

	echo "New Version [major|minor|patch]:"
	npm version

	npm publish

	cd ../
done

git push --follow-tags
