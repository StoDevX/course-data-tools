git pull --rebase

echo "Prior version:" `npm version | grep sto-courses`

read -p "Version: " version; \
	npm version $version --message "v%s"

git push --follow-tags

npm publish
