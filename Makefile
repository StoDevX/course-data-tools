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

prepare-install:
	rm -rf details/
	rm -rf raw_xml/
	# rm -rf playground/
	# rm -rf scripts/
	# rm getData.py
	# rm .gitattributes .gitignore
	# rm README.md
	# rm Makefile
