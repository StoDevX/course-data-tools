def parse_notes(course):
    if course['notes'] and 'Will also meet' in course['notes']:
        info = dedent(f'''
            [{course['year']}{course['semester']}] {course['type'][0]} ({'/'.join(course['departments'])} {course['number']} | {course['clbid']} {course['crsid']}):
            \t{course['notes']}
            \t{course['times']} {course['locations']}
        ''')

        # get the timestring and location string out of the notes field
        notes_into_time_and_location_regex = r'.*meet ([MTWF][/-]?.*) in (.*)\.'
        results = re.search(notes_into_time_and_location_regex,
                            course['notes'])
        extra_times, extra_locations = results.groups()
        # print(info + '\n\t' + 'regex matches:', [extra_times, extra_locations])
        print(extra_times)

        # split_time_regex =

        split_location_regex = r'(\w+ ?\d+)(?: or ?(\w+ ?\d+))?'

        # expandedDays = {
        #   'M':  'Mo',
        #   'T':  'Tu',
        #   'W':  'We',
        #   'Th': 'Th',
        #   'F':  'Fr'
        # }

        # listOfDays = []

        # if '-' in daystring:
        #   # M-F, M-Th, T-F
        #   sequence = ['M', 'T', 'W', 'Th', 'F']
        #   startDay = daystring.split('-')[0]
        #   endDay = daystring.split('-')[1]
        #   listOfDays = sequence.slice(
        #       sequence.indexOf(startDay),
        #       sequence.indexOf(endDay) + 1
        #   )
        # else:
        #   # MTThFW
        #   spacedOutDays = daystring.replace(/([a-z]*)([A-Z])/g, '$1 $2')
        #   # The regex sticks an extra space at the front. trim() it.
        #   spacedOutDays = spacedOutDays.trim()
        #   listOfDays = spacedOutDays.split(' ')

        # # 'M' => 'Mo'
        # return list(map(lambda day: expandedDays[day], listOfDays))
