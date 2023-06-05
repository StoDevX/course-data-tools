import re

WEEKDAYS = {
    "M": "Mo",
    "T": "Tu",
    "W": "We",
    "Th": "Th",
    "F": "Fr",
}

DAY_SEQUENCE = ["M", "T", "W", "Th", "F"]

AM_PM_REGEX = re.compile(r"([AP])\.?M\.?", re.IGNORECASE)


def parse_timestring(timestring):
    daystring, timestring = timestring.split(" ")

    days = find_days(daystring)
    time = find_time(timestring)

    # ensure that the numbers are padded to 4-char width
    start = str(time["start"]).rjust(4, "0")
    end = str(time["end"]).rjust(4, "0")

    start = start[:2] + ":" + start[2:]
    end = end[:2] + ":" + end[2:]

    return [
        {
            "day": day,
            "start": start,
            "end": end,
        }
        for day in days
    ]


def find_days(daystring):
    listOfDays = []

    if "-" in daystring:
        # M-F, M-Th, T-F
        startDay, endDay = daystring.split("-")
        listOfDays = DAY_SEQUENCE[
            DAY_SEQUENCE.index(startDay) : DAY_SEQUENCE.index(endDay) + 1
        ]
    else:
        # MTThFW or M/T/Th/F/W
        spacedOutDays = re.sub(r"([A-Z][a-z]?)\/?", r"\1 ", daystring)

        # The regex sticks an extra space at the end. Remove it.
        spacedOutDays = spacedOutDays.strip()

        listOfDays = spacedOutDays.split(" ")

    # 'M' => 'Mo'
    return [WEEKDAYS[day] for day in listOfDays]


# Clean a timestring segment by uppercasing and trimming it.
def clean_timestring_segment(segment):
    return segment.upper().strip()


# Takes a timestring  and turns it into an object with 24-hour time.
# "800-925" => {start: 800, end: 925}
def find_time(timestring):
    cleanedTimestring = re.sub(r":", "", timestring)  # 8:00-9:25 => 800-925

    endsInPM = False
    startsInAM = False

    # Split the string apart and clean it up.
    start, end = [
        clean_timestring_segment(segment) for segment in cleanedTimestring.split("-")
    ]

    # There are a few courses that both start and end at 00.
    # I've decided that they mean that it's an all-day course.
    if start == "00" and end == "00":
        return {"start": 0, "end": 2359}

    # Grab the AM/PM indicator, if present, and strip it off.
    am = AM_PM_REGEX.search(start)
    pm = AM_PM_REGEX.search(end)

    if am:
        startsInAM = True
        start = start[: am.start()]

    if pm:
        endsInPM = True
        end = end[: pm.start()]

    # Turn the string into integers
    startTime = int(start)
    endTime = int(end)

    # ASSERT: There are no courses that end at or before 8am.
    if endTime <= 800:
        # 'M 0100-0400'
        endsInPM = True

    # ASSERT: Courses cannot end before they start.
    # Therefore, it must end in the afternoon.
    if endTime < startTime:
        # cannot end before it starts
        endsInPM = True
        endTime += 1200

    # ASSERT: In 24-hour time, PM is > 1200.
    if endsInPM and endTime < 1200:
        endTime += 1200

    # ASSERT: There are no courses that end in the afternoon,
    # start before 700 hours, and don't start in the morning.
    # COMMENT: uh, what?
    if endsInPM and startTime < 700 and not startsInAM:
        startTime += 1200

    # ASSERT: There are no courses that take longer than 10 hours
    # and don't start in the morning.
    if (endTime - startTime) > 1000 and not startsInAM:
        # There are no courses that take this long.
        # There are some 6-hour ones in interim, though.
        startTime += 1200

    return {
        "start": startTime,
        "end": endTime,
    }
