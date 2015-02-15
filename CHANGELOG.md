# Changelog for Course Data
This does not keep track of the changes in the data; rather, it keeps track of the changes in the tooling and formats of the data.

## 4.0.0
- [x] Broke files stored in the repo into individual files
	- they're stored under the same 10,000-strong directory structure as the details files
- [x] Track revision data within the courses
- [x] Extracted almost all of getData into seperate scripts
- [ ] Postpone generation of the final JSON files until `npm publish`
- [x] Added flag `--no-revisions` to prevent searching of revisions
- [x] If `name` and `title` are equal, don't emit the title
- [x] Embedded terms into the courses in the XML files
