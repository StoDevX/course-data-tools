.PHONY: update publish dist

update:
	./getData.py --force

full-update:
	rm -rf details/
	make update

fast-update:
	# date +"%Y" is the current year
	./getData.py --force --years `date +"%Y"`

publish:
	git pull --rebase

	@echo
	@echo "Prior version: `npm version | grep sto-courses`"
	@echo "<major>.<minor>.<date-updated>.<patch>"
	@echo "Increment numbers as needed."
	@echo

	read -p "Version: "  version; \
  npm version $$version --message "v%s"

	git push --follow-tags

	npm publish
