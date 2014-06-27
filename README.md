- [ ] TODO: Redo profs, depts, times, places, and gereqs as foreign keys to other tables in the db.
- [ ] TODO: Implement the new CLI for getData.py

## New CLI for getData.py

	$ ./getData.py --years 2012 2013 2014 --terms 19941 19911
	Terms: 1991[1], 1994[1], 2012[1, 2, 3, 4, 5], 2013[1, 2, 3, 4, 5], 2014[1, 2, 3]
	
	Using cache for 1994[1], 2012[1, 2, 3, 4, 5], 2013[2, 4, 5], 2014[1, 2, 3].
	Need to request 1991[1], 2013[1, 3].
	
	1991-1: No data.
	
	1994-1: Done.
	
	2012-1: Done.
	2012-2: Done.
	2012-3: Done.
	2012-4: Done.
	2012-5: Done.
	
	2013-1: Requesting…
	2013-2: Editing… (75% done - 450/600)
	2013-3: Detailing… (35% done - 35/100)
	2013-4: Done.
	2013-5: Done.
	
	2014-1: Editing…
	2014-2: Done.
	2014-3: Waiting…
	
	Status: 66% - 10/15 terms completed.
