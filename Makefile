.PHONY: update publish dist

update:
	# date +"%Y" is the current year
	./getData.py --force --years `date +"%Y"`

publish:
	git pull --rebase

	@echo
	@echo "Prior version: `npm version | grep gobbldygook-course-data`"
	@echo "<major>.<minor>.<date-updated>.<patch>"
	@echo "Increment numbers as needed."
	@echo

	read -p "Version: "  version; \
  npm version $$version --message "v%s"

	git push --follow-tags

	node scripts/create-github-release.js

dist:
	mkdir -p dist/
	tar -c terms info.json package.json | gzip > dist/data.tar.gz

