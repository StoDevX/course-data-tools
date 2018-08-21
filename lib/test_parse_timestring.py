from .parse_timestring import parse_timestring, clean_timestring_segment, find_days, find_time


def test_parse_timestring():
	assert parse_timestring("MWF 300-415") == [
		{'day': 'Mo', 'start': '15:00', 'end': '16:15'},
		{'day': 'We', 'start': '15:00', 'end': '16:15'},
		{'day': 'Fr', 'start': '15:00', 'end': '16:15'},
	]

	assert parse_timestring("MWF 900-1015") == [
		{'day': 'Mo', 'start': '09:00', 'end': '10:15'},
		{'day': 'We', 'start': '09:00', 'end': '10:15'},
		{'day': 'Fr', 'start': '09:00', 'end': '10:15'},
	]


def test_clean_timestring_segment():
	assert clean_timestring_segment('    800AM   ') == '800AM'
	assert clean_timestring_segment('800am') == '800AM'


def test_find_days_unambiguous():
	'''turns the day abbreviations into a list of unambiguous days'''
	assert find_days('M') == ['Mo']
	assert find_days('T') == ['Tu']
	assert find_days('W') == ['We']
	assert find_days('Th') == ['Th']
	assert find_days('F') == ['Fr']


def test_find_days_hyphenated():
	'''handles hyphenated day sequences'''
	assert find_days('M-F') == ['Mo', 'Tu', 'We', 'Th', 'Fr']
	assert find_days('M-Th') == ['Mo', 'Tu', 'We', 'Th']
	assert find_days('T-F') == ['Tu', 'We', 'Th', 'Fr']
	assert find_days('M-T') == ['Mo', 'Tu']


def test_find_days_stringy():
	'''handles strings of letters correctly'''
	assert find_days('MTThFW') == ['Mo', 'Tu', 'Th', 'Fr', 'We']
	assert find_days('MTTh') == ['Mo', 'Tu', 'Th']
	assert find_days('ThFMT') == ['Th', 'Fr', 'Mo', 'Tu']


def test_find_days_sis_variants():
	'''correctly parses every variant that the SIS contains'''
	assert find_days('F') == ['Fr']
	assert find_days('M') == ['Mo']
	assert find_days('M-F') == ['Mo', 'Tu', 'We', 'Th', 'Fr']
	assert find_days('M-Th') == ['Mo', 'Tu', 'We', 'Th']
	assert find_days('MF') == ['Mo', 'Fr']
	assert find_days('MFW') == ['Mo', 'Fr', 'We']
	assert find_days('MT') == ['Mo', 'Tu']
	assert find_days('MTF') == ['Mo', 'Tu', 'Fr']
	assert find_days('MTTh') == ['Mo', 'Tu', 'Th']
	assert find_days('MTThF') == ['Mo', 'Tu', 'Th', 'Fr']
	assert find_days('MTThFW') == ['Mo', 'Tu', 'Th', 'Fr', 'We']
	assert find_days('MTW') == ['Mo', 'Tu', 'We']
	assert find_days('MTWF') == ['Mo', 'Tu', 'We', 'Fr']
	assert find_days('MTh') == ['Mo', 'Th']
	assert find_days('MW') == ['Mo', 'We']
	assert find_days('MWF') == ['Mo', 'We', 'Fr']
	assert find_days('MWFT') == ['Mo', 'We', 'Fr', 'Tu']
	assert find_days('MWTh') == ['Mo', 'We', 'Th']
	assert find_days('MWThF') == ['Mo', 'We', 'Th', 'Fr']
	assert find_days('T') == ['Tu']
	assert find_days('T-F') == ['Tu', 'We', 'Th', 'Fr']
	assert find_days('TTh') == ['Tu', 'Th']
	assert find_days('TThF') == ['Tu', 'Th', 'Fr']
	assert find_days('TW') == ['Tu', 'We']
	assert find_days('TWF') == ['Tu', 'We', 'Fr']
	assert find_days('TWTh') == ['Tu', 'We', 'Th']
	assert find_days('Th') == ['Th']
	assert find_days('W') == ['We']
	assert find_days('WF') == ['We', 'Fr']
	assert find_days('WTh') == ['We', 'Th']


def test_find_times_time_shorthand():
	'''turns the absurd time shorthand into unambiguous 24-hour time'''
	assert find_time('0200-0400PM') == {'start': 1400, 'end': 1600}


def test_find_times_colons():
	'''handles times with colons'''
	assert find_time('5:00-9:00') == {'start': 500, 'end': 900}
	assert find_time('7:00-9:00') == {'start': 700, 'end': 900}
	assert find_time('8:00-9:00') == {'start': 800, 'end': 900}

	assert find_time('1:00-3:00PM') == {'start': 1300, 'end': 1500}
	assert find_time('8:00-9:25') == {'start': 800, 'end': 925}


def test_find_times_all_day_times():
	'''handles all-day times'''
	assert find_time('00-00') == {'start': 0, 'end': 2359}


def test_find_times_afternoon():
	'''handles both courses that should and courses that do end in the afternoon'''
	assert find_time('0100-0400') == {'start': 1300, 'end': 1600}
	assert find_time('0100-0400PM') == {'start': 1300, 'end': 1600}


def test_find_times_am():
	'''handles coures with explicit AM notation'''
	assert find_time('1100AM-0400PM') == {'start': 1100, 'end': 1600}
	# TODO: this is wierd
	assert find_time('100AM-0400') == {'start': 100, 'end': 1600}


def test_find_times_sis_variants():
	'''handles every variant that the SIS contains'''
	assert find_time('5:00-9:00') == {'start': 500, 'end': 900}
	assert find_time('7:00-9:00') == {'start': 700, 'end': 900}
	assert find_time('8:00-9:00') == {'start': 800, 'end': 900}

	# all day courses!
	assert find_time('00-00') == {'start': 0, 'end': 2359}

	assert find_time('0100-0200PM') == {'start': 1300, 'end': 1400}
	assert find_time('0100-0215PM') == {'start': 1300, 'end': 1415}
	assert find_time('0100-0230PM') == {'start': 1300, 'end': 1430}
	assert find_time('0100-0300PM') == {'start': 1300, 'end': 1500}
	assert find_time('0100-0330PM') == {'start': 1300, 'end': 1530}
	assert find_time('0100-0400'  ) == {'start': 1300, 'end': 1600}
	assert find_time('0100-0400PM') == {'start': 1300, 'end': 1600}
	assert find_time('0100-0500PM') == {'start': 1300, 'end': 1700}

	assert find_time('0110-0245PM') == {'start': 1310, 'end': 1445}
	assert find_time('0110-0340PM') == {'start': 1310, 'end': 1540}

	assert find_time('0115-0159PM') == {'start': 1315, 'end': 1359}
	assert find_time('0115-0200PM') == {'start': 1315, 'end': 1400}
	assert find_time('0115-0215PM') == {'start': 1315, 'end': 1415}
	assert find_time('0115-0230PM') == {'start': 1315, 'end': 1430}
	assert find_time('0115-0245PM') == {'start': 1315, 'end': 1445}
	assert find_time('0115-0300PM') == {'start': 1315, 'end': 1500}

	assert find_time('0120-0215PM') == {'start': 1320, 'end': 1415}
	assert find_time('0120-0220PM') == {'start': 1320, 'end': 1420}
	assert find_time('0120-0225PM') == {'start': 1320, 'end': 1425}
	assert find_time('0120-0245PM') == {'start': 1320, 'end': 1445}
	assert find_time('0120-0250PM') == {'start': 1320, 'end': 1450}
	assert find_time('0120-0255PM') == {'start': 1320, 'end': 1455}
	assert find_time('0120-0320PM') == {'start': 1320, 'end': 1520}
	assert find_time('0120-0320'  ) == {'start': 1320, 'end': 1520}
	assert find_time('0120-0330PM') == {'start': 1320, 'end': 1530}
	assert find_time('0120-0350PM') == {'start': 1320, 'end': 1550}
	assert find_time('0120-0355PM') == {'start': 1320, 'end': 1555}
	assert find_time('0120-0420PM') == {'start': 1320, 'end': 1620}
	assert find_time('0120-0450PM') == {'start': 1320, 'end': 1650}
	assert find_time('0120-0520PM') == {'start': 1320, 'end': 1720}

	assert find_time('0130-0230PM') == {'start': 1330, 'end': 1430}
	assert find_time('0130-0300PM') == {'start': 1330, 'end': 1500}
	assert find_time('0130-0330PM') == {'start': 1330, 'end': 1530}
	assert find_time('0130-0400PM') == {'start': 1330, 'end': 1600}
	assert find_time('0130-0430PM') == {'start': 1330, 'end': 1630}
	assert find_time('0130-0530PM') == {'start': 1330, 'end': 1730}

	assert find_time('0140-0440PM') == {'start': 1340, 'end': 1640}

	assert find_time('0145-0245PM') == {'start': 1345, 'end': 1445}
	assert find_time('0145-0300PM') == {'start': 1345, 'end': 1500}


	assert find_time('0200-0245PM') == {'start': 1400, 'end': 1445}
	assert find_time('0200-0255PM') == {'start': 1400, 'end': 1455}
	assert find_time('0200-0300PM') == {'start': 1400, 'end': 1500}
	assert find_time('0200-0320PM') == {'start': 1400, 'end': 1520}
	assert find_time('0200-0325PM') == {'start': 1400, 'end': 1525}
	assert find_time('0200-0330PM') == {'start': 1400, 'end': 1530}
	assert find_time('0200-0335PM') == {'start': 1400, 'end': 1535}
	assert find_time('0200-0340PM') == {'start': 1400, 'end': 1540}
	assert find_time('0200-0400PM') == {'start': 1400, 'end': 1600}
	assert find_time('0200-0430PM') == {'start': 1400, 'end': 1630}
	assert find_time('0200-0500PM') == {'start': 1400, 'end': 1700}
	assert find_time('0200-0600PM') == {'start': 1400, 'end': 1800}

	assert find_time('0205-0255PM') == {'start': 1405, 'end': 1455}
	assert find_time('0205-0335PM') == {'start': 1405, 'end': 1535}

	assert find_time('0215-0310PM') == {'start': 1415, 'end': 1510}
	assert find_time('0215-0315PM') == {'start': 1415, 'end': 1515}
	assert find_time('0215-0335PM') == {'start': 1415, 'end': 1535}
	assert find_time('0215-0405PM') == {'start': 1415, 'end': 1605}
	assert find_time('0215-0415PM') == {'start': 1415, 'end': 1615}
	assert find_time('0215-0445PM') == {'start': 1415, 'end': 1645}
	assert find_time('0215-0445  ') == {'start': 1415, 'end': 1645}
	assert find_time('0215-0500PM') == {'start': 1415, 'end': 1700}
	assert find_time('0215-0505PM') == {'start': 1415, 'end': 1705}
	assert find_time('0215-0515PM') == {'start': 1415, 'end': 1715}

	assert find_time('0220-0520PM') == {'start': 1420, 'end': 1720}

	assert find_time('0225-0315PM') == {'start': 1425, 'end': 1515}
	assert find_time('0225-0455PM') == {'start': 1425, 'end': 1655}

	assert find_time('0230-0325PM') == {'start': 1430, 'end': 1525}
	assert find_time('0230-0330PM') == {'start': 1430, 'end': 1530}
	assert find_time('0230-0400PM') == {'start': 1430, 'end': 1600}
	assert find_time('0230-0415PM') == {'start': 1430, 'end': 1615}
	assert find_time('0230-0430PM') == {'start': 1430, 'end': 1630}
	assert find_time('0230-0500PM') == {'start': 1430, 'end': 1700}
	assert find_time('0230-0530PM') == {'start': 1430, 'end': 1730}

	assert find_time('0240-0335PM') == {'start': 1440, 'end': 1535}

	assert find_time('0255-0340PM') == {'start': 1455, 'end': 1540}
	assert find_time('0256-0340PM') == {'start': 1456, 'end': 1540}


	assert find_time('0300-0400PM') == {'start': 1500, 'end': 1600}
	assert find_time('0300-0430PM') == {'start': 1500, 'end': 1630}
	assert find_time('0300-0500PM') == {'start': 1500, 'end': 1700}
	assert find_time('0300-0530PM') == {'start': 1500, 'end': 1730}
	assert find_time('0300-0600PM') == {'start': 1500, 'end': 1800}

	assert find_time('0305-0400PM') == {'start': 1505, 'end': 1600}
	assert find_time('0305-0405PM') == {'start': 1505, 'end': 1605}
	assert find_time('0305-0415PM') == {'start': 1505, 'end': 1615}
	assert find_time('0305-0430PM') == {'start': 1505, 'end': 1630}

	assert find_time('0310-0415PM') == {'start': 1510, 'end': 1615}
	assert find_time('0310-0420PM') == {'start': 1510, 'end': 1620}

	assert find_time('0315-0415PM') == {'start': 1515, 'end': 1615}
	assert find_time('0315-0445PM') == {'start': 1515, 'end': 1645}
	assert find_time('0315-0515PM') == {'start': 1515, 'end': 1715}

	assert find_time('0320-0415PM') == {'start': 1520, 'end': 1615}
	assert find_time('0320-0420PM') == {'start': 1520, 'end': 1620}

	assert find_time('0330-0425PM') == {'start': 1530, 'end': 1625}
	assert find_time('0330-0430PM') == {'start': 1530, 'end': 1630}
	assert find_time('0330-0500PM') == {'start': 1530, 'end': 1700}
	assert find_time('0330-0530PM') == {'start': 1530, 'end': 1730}
	assert find_time('0330-0600PM') == {'start': 1530, 'end': 1800}

	assert find_time('0335-0530PM') == {'start': 1535, 'end': 1730}
	assert find_time('0335-0605PM') == {'start': 1535, 'end': 1805}

	assert find_time('0340-0610PM') == {'start': 1540, 'end': 1810}

	assert find_time('0345-0455PM') == {'start': 1545, 'end': 1655}
	assert find_time('0345-0515PM') == {'start': 1545, 'end': 1715}
	assert find_time('0345-0545PM') == {'start': 1545, 'end': 1745}

	assert find_time('0350-0450PM') == {'start': 1550, 'end': 1650}

	assert find_time('0355-0450PM') == {'start': 1555, 'end': 1650}
	assert find_time('0355-0515PM') == {'start': 1555, 'end': 1715}


	assert find_time('0400-0500PM') == {'start': 1600, 'end': 1700}
	assert find_time('0400-0530PM') == {'start': 1600, 'end': 1730}
	assert find_time('0400-0600PM') == {'start': 1600, 'end': 1800}

	assert find_time('0405-0530PM') == {'start': 1605, 'end': 1730}

	assert find_time('0430-0530PM') == {'start': 1630, 'end': 1730}
	assert find_time('0430-0600PM') == {'start': 1630, 'end': 1800}

	assert find_time('0450-0545PM') == {'start': 1650, 'end': 1745}
	assert find_time('0450-0600PM') == {'start': 1650, 'end': 1800}
	assert find_time('0450-0615PM') == {'start': 1650, 'end': 1815}


	assert find_time('0500-0600PM') == {'start': 1700, 'end': 1800}
	assert find_time('0500-0730PM') == {'start': 1700, 'end': 1930}

	assert find_time('0505-0615PM') == {'start': 1705, 'end': 1815}

	assert find_time('0530-0630PM') == {'start': 1730, 'end': 1830}


	assert find_time('0600-0655PM') == {'start': 1800, 'end': 1855}
	assert find_time('0600-0700PM') == {'start': 1800, 'end': 1900}
	assert find_time('0600-0730PM') == {'start': 1800, 'end': 1930}
	assert find_time('0600-0800PM') == {'start': 1800, 'end': 2000}
	assert find_time('0600-0830PM') == {'start': 1800, 'end': 2030}
	assert find_time('0600-0900PM') == {'start': 1800, 'end': 2100}
	assert find_time('0600-1000PM') == {'start': 1800, 'end': 2200}

	assert find_time('0630-0730PM') == {'start': 1830, 'end': 1930}
	assert find_time('0630-0800PM') == {'start': 1830, 'end': 2000}
	assert find_time('0630-0830PM') == {'start': 1830, 'end': 2030}
	assert find_time('0630-0900PM') == {'start': 1830, 'end': 2100}
	assert find_time('0630-0930PM') == {'start': 1830, 'end': 2130}

	assert find_time('0645-0745') == {'start': 1845, 'end': 1945}
	assert find_time('0645-0745PM') == {'start': 1845, 'end': 1945}


	assert find_time('0700-0230PM') == {'start': 700, 'end': 1430}
	assert find_time('0700-0300PM') == {'start': 700, 'end': 1500}
	assert find_time('0700-0330PM') == {'start': 700, 'end': 1530}
	assert find_time('0700-0755PM') == {'start': 1900, 'end': 1955}
	assert find_time('0700-0800') == {'start': 1900, 'end': 2000}
	assert find_time('0700-0800PM') == {'start': 1900, 'end': 2000}
	assert find_time('0700-0830PM') == {'start': 1900, 'end': 2030}
	assert find_time('0700-0900') == {'start': 700, 'end': 900}
	assert find_time('0700-0900PM') == {'start': 1900, 'end': 2100}
	assert find_time('0700-0930PM') == {'start': 1900, 'end': 2130}
	assert find_time('0700-1000PM') == {'start': 1900, 'end': 2200}
	assert find_time('0700-1230PM') == {'start': 700, 'end': 1230}

	assert find_time('0730-0100PM') == {'start': 730, 'end': 1300}
	assert find_time('0730-0230PM') == {'start': 730, 'end': 1430}
	assert find_time('0730-0330PM') == {'start': 730, 'end': 1530}
	assert find_time('0730-0400PM') == {'start': 730, 'end': 1600}
	assert find_time('0730-0900PM') == {'start': 1930, 'end': 2100}
	assert find_time('0730-0925') == {'start': 730, 'end': 925}
	assert find_time('0730-0930PM') == {'start': 1930, 'end': 2130}
	assert find_time('0730-1000') == {'start': 730, 'end': 1000}
	assert find_time('0730-1000PM') == {'start': 1930, 'end': 2200}
	assert find_time('0730-1200PM') == {'start': 730, 'end': 1200}


	assert find_time('0800-0100PM') == {'start': 800, 'end': 1300}
	assert find_time('0800-0400PM') == {'start': 800, 'end': 1600}
	assert find_time('0800-0850') == {'start': 800, 'end': 850}
	assert find_time('0800-0855') == {'start': 800, 'end': 855}
	assert find_time('0800-0900') == {'start': 800, 'end': 900}
	assert find_time('0800-0900PM') == {'start': 2000, 'end': 2100}
	assert find_time('0800-0905') == {'start': 800, 'end': 905}
	assert find_time('0800-0920') == {'start': 800, 'end': 920}
	assert find_time('0800-0925') == {'start': 800, 'end': 925}
	assert find_time('0800-0930') == {'start': 800, 'end': 930}
	assert find_time('0800-0935') == {'start': 800, 'end': 935}
	assert find_time('0800-1000') == {'start': 800, 'end': 1000}
	assert find_time('0800-1000PM') == {'start': 2000, 'end': 2200}
	assert find_time('0800-1030') == {'start': 800, 'end': 1030}
	assert find_time('0800-1050') == {'start': 800, 'end': 1050}
	assert find_time('0800-1100') == {'start': 800, 'end': 1100}
	assert find_time('0800-1130') == {'start': 800, 'end': 1130}
	assert find_time('0800-1200') == {'start': 800, 'end': 1200}
	assert find_time('0800-1200PM') == {'start': 800, 'end': 1200}

	assert find_time('0820-1050') == {'start': 820, 'end': 1050}

	assert find_time('0825-0920') == {'start': 825, 'end': 920}

	assert find_time('0830-0300PM') == {'start': 830, 'end': 1500}
	assert find_time('0830-0925') == {'start': 830, 'end': 925}
	assert find_time('0830-1000') == {'start': 830, 'end': 1000}
	assert find_time('0830-1100') == {'start': 830, 'end': 1100}

	assert find_time('0845-1000') == {'start': 845, 'end': 1000}

	assert find_time('0850-1050') == {'start': 850, 'end': 1050}

	assert find_time('0855-0950') == {'start': 855, 'end': 950}


	assert find_time('0900-0100PM') == {'start': 900, 'end': 1300}
	assert find_time('0900-0200PM') == {'start': 900, 'end': 1400}
	assert find_time('0900-0300PM') == {'start': 900, 'end': 1500}
	assert find_time('0900-0330PM') == {'start': 900, 'end': 1530}
	assert find_time('0900-0400PM') == {'start': 900, 'end': 1600}
	assert find_time('0900-0500PM') == {'start': 900, 'end': 1700}
	assert find_time('0900-0955') == {'start': 900, 'end': 955}
	assert find_time('0900-1000') == {'start': 900, 'end': 1000}
	assert find_time('0900-1000PM') == {'start': 2100, 'end': 2200}
	assert find_time('0900-1050') == {'start': 900, 'end': 1050}
	assert find_time('0900-1100') == {'start': 900, 'end': 1100}
	assert find_time('0900-1200PM') == {'start': 900, 'end': 1200}
	assert find_time('0900-1215PM') == {'start': 900, 'end': 1215}
	assert find_time('0900-1230PM') == {'start': 900, 'end': 1230}

	assert find_time('0905-1000') == {'start': 905, 'end': 1000}
	assert find_time('0905-1140') == {'start': 905, 'end': 1140}

	assert find_time('0915-1115') == {'start': 915, 'end': 1115}

	assert find_time('0930-1025') == {'start': 930, 'end': 1025}
	assert find_time('0930-1030') == {'start': 930, 'end': 1030}
	assert find_time('0930-1045') == {'start': 930, 'end': 1045}
	assert find_time('0930-1050') == {'start': 930, 'end': 1050}
	assert find_time('0930-1100') == {'start': 930, 'end': 1100}

	assert find_time('0935-1030') == {'start': 935, 'end': 1030}
	assert find_time('0935-1035') == {'start': 935, 'end': 1035}
	assert find_time('0935-1050') == {'start': 935, 'end': 1050}
	assert find_time('0935-1100') == {'start': 935, 'end': 1100}
	assert find_time('0935-1110') == {'start': 935, 'end': 1110}

	assert find_time('0955-1050') == {'start': 955, 'end': 1050}


	assert find_time('1000-1055') == {'start': 1000, 'end': 1055}
	assert find_time('1000-1130') == {'start': 1000, 'end': 1130}
	assert find_time('1000-1200') == {'start': 1000, 'end': 1200}
	assert find_time('1000-1200PM') == {'start': 1000, 'end': 1200}
	assert find_time('1000-1230PM') == {'start': 1000, 'end': 1230}

	assert find_time('1005-1100') == {'start': 1005, 'end': 1100}

	assert find_time('1010-1100') == {'start': 1010, 'end': 1100}

	assert find_time('1030-1145') == {'start': 1030, 'end': 1145}
	assert find_time('1030-1200PM') == {'start': 1030, 'end': 1200}
	assert find_time('1030-1230PM') == {'start': 1030, 'end': 1230}

	assert find_time('1040-0100PM') == {'start': 1040, 'end': 1300}
	assert find_time('1040-0110PM') == {'start': 1040, 'end': 1310}
	assert find_time('1040-0200PM') == {'start': 1040, 'end': 1400}
	assert find_time('1040-0300PM') == {'start': 1040, 'end': 1500}
	assert find_time('1040-0330PM') == {'start': 1040, 'end': 1530}
	assert find_time('1040-0500PM') == {'start': 1040, 'end': 1700}
	assert find_time('1040-1130') == {'start': 1040, 'end': 1130}
	assert find_time('1040-1135') == {'start': 1040, 'end': 1135}
	assert find_time('1040-1140') == {'start': 1040, 'end': 1140}
	assert find_time('1040-1150') == {'start': 1040, 'end': 1150}
	assert find_time('1040-1200') == {'start': 1040, 'end': 1200}
	assert find_time('1040-1200PM') == {'start': 1040, 'end': 1200}
	assert find_time('1040-1210PM') == {'start': 1040, 'end': 1210}
	assert find_time('1040-1215PM') == {'start': 1040, 'end': 1215}
	assert find_time('1040-1220PM') == {'start': 1040, 'end': 1220}
	assert find_time('1040-1230PM') == {'start': 1040, 'end': 1230}
	assert find_time('1040-1240PM') == {'start': 1040, 'end': 1240}

	assert find_time('1045-0100PM') == {'start': 1045, 'end': 1300}
	assert find_time('1045-0115PM') == {'start': 1045, 'end': 1315}
	assert find_time('1045-0145PM') == {'start': 1045, 'end': 1345}
	assert find_time('1045-1135') == {'start': 1045, 'end': 1135}
	assert find_time('1045-1140') == {'start': 1045, 'end': 1140}
	assert find_time('1045-1145') == {'start': 1045, 'end': 1145}
	assert find_time('1045-1150') == {'start': 1045, 'end': 1150}
	assert find_time('1045-1200PM') == {'start': 1045, 'end': 1200}
	assert find_time('1045-1215PM') == {'start': 1045, 'end': 1215}
	assert find_time('1045-1230PM') == {'start': 1045, 'end': 1230}
	assert find_time('1045-1245PM') == {'start': 1045, 'end': 1245}
	assert find_time('1045-1345PM') == {'start': 1045, 'end': 1345}

	assert find_time('1050-1220PM') == {'start': 1050, 'end': 1220}


	assert find_time('1100-0130PM') == {'start': 1100, 'end': 1330}
	assert find_time('1100-0200PM') == {'start': 1100, 'end': 1400}
	assert find_time('1100-1200PM') == {'start': 1100, 'end': 1200}

	assert find_time('1110-1240PM') == {'start': 1110, 'end': 1240}

	assert find_time('1125-0245PM') == {'start': 1125, 'end': 1445}

	assert find_time('1130-0130PM') == {'start': 1130, 'end': 1330}
	assert find_time('1130-0200PM') == {'start': 1130, 'end': 1400}
	assert find_time('1130-0230PM') == {'start': 1130, 'end': 1430}

	assert find_time('1140-1230PM') == {'start': 1140, 'end': 1230}
	assert find_time('1140-1240PM') == {'start': 1140, 'end': 1240}

	assert find_time('1145-0100PM') == {'start': 1145, 'end': 1300}
	assert find_time('1145-0110PM') == {'start': 1145, 'end': 1310}
	assert find_time('1145-0115PM') == {'start': 1145, 'end': 1315}
	assert find_time('1145-0120PM') == {'start': 1145, 'end': 1320}
	assert find_time('1145-0145PM') == {'start': 1145, 'end': 1345}
	assert find_time('1145-0200PM') == {'start': 1145, 'end': 1400}
	assert find_time('1145-0215PM') == {'start': 1145, 'end': 1415}
	assert find_time('1145-0245') == {'start': 1145, 'end': 1445}
	assert find_time('1145-0245PM') == {'start': 1145, 'end': 1445}
	assert find_time('1145-0345PM') == {'start': 1145, 'end': 1545}
	assert find_time('1145-1240') == {'start': 1145, 'end': 1240}
	assert find_time('1145-1240PM') == {'start': 1145, 'end': 1240}
	assert find_time('1145-1245PM') == {'start': 1145, 'end': 1245}
	assert find_time('1145-1250PM') == {'start': 1145, 'end': 1250}

	assert find_time('1150-0110PM') == {'start': 1150, 'end': 1310}
	assert find_time('1150-0150PM') == {'start': 1150, 'end': 1350}
	assert find_time('1150-0220PM') == {'start': 1150, 'end': 1420}
	assert find_time('1150-0250PM') == {'start': 1150, 'end': 1450}
	assert find_time('1150-0255PM') == {'start': 1150, 'end': 1455}
	assert find_time('1150-0350PM') == {'start': 1150, 'end': 1550}
	assert find_time('1150-1240PM') == {'start': 1150, 'end': 1240}
	assert find_time('1150-1245PM') == {'start': 1150, 'end': 1245}
	assert find_time('1150-1255PM') == {'start': 1150, 'end': 1255}

	assert find_time('1155-1250PM') == {'start': 1155, 'end': 1250}


	assert find_time('1200-0100PM') == {'start': 1200, 'end': 1300}
	assert find_time('1200-0150PM') == {'start': 1200, 'end': 1350}
	assert find_time('1200-0200PM') == {'start': 1200, 'end': 1400}
	assert find_time('1200-0230PM') == {'start': 1200, 'end': 1430}
	assert find_time('1200-0300PM') == {'start': 1200, 'end': 1500}
	assert find_time('1200-0400PM') == {'start': 1200, 'end': 1600}

	assert find_time('1215-0245PM') == {'start': 1215, 'end': 1445}

	assert find_time('1220-0150PM') == {'start': 1220, 'end': 1350}
	assert find_time('1220-0250PM') == {'start': 1220, 'end': 1450}

	assert find_time('1230-0100PM') == {'start': 1230, 'end': 1300}
	assert find_time('1230-0200PM') == {'start': 1230, 'end': 1400}
	assert find_time('1230-0230PM') == {'start': 1230, 'end': 1430}
	assert find_time('1230-0300PM') == {'start': 1230, 'end': 1500}
	assert find_time('1230-0330PM') == {'start': 1230, 'end': 1530}
	assert find_time('1230-0400PM') == {'start': 1230, 'end': 1600}
	assert find_time('1230-0430PM') == {'start': 1230, 'end': 1630}

	assert find_time('1235-0235PM') == {'start': 1235, 'end': 1435}

	assert find_time('1240-0330PM') == {'start': 1240, 'end': 1530}
	assert find_time('1240-0340PM') == {'start': 1240, 'end': 1540}

	assert find_time('1245-0105PM') == {'start': 1245, 'end': 1305}
	assert find_time('1245-0140PM') == {'start': 1245, 'end': 1340}
	assert find_time('1245-0145PM') == {'start': 1245, 'end': 1345}
	assert find_time('1245-0205PM') == {'start': 1245, 'end': 1405}
	assert find_time('1245-0215PM') == {'start': 1245, 'end': 1415}
	assert find_time('1245-0230PM') == {'start': 1245, 'end': 1430}
	assert find_time('1245-0245PM') == {'start': 1245, 'end': 1445}
	assert find_time('1245-0300PM') == {'start': 1245, 'end': 1500}
	assert find_time('1245-0315PM') == {'start': 1245, 'end': 1515}
	assert find_time('1245-0335PM') == {'start': 1245, 'end': 1535}
	assert find_time('1245-0345PM') == {'start': 1245, 'end': 1545}
	assert find_time('1245-1545PM') == {'start': 1245, 'end': 1545}

	assert find_time('1250-0320PM') == {'start': 1250, 'end': 1520}
	assert find_time('1250-0350PM') == {'start': 1250, 'end': 1550}

	assert find_time('1255-0110PM') == {'start': 1255, 'end': 1310}
	assert find_time('1255-0140PM') == {'start': 1255, 'end': 1340}
	assert find_time('1255-0145PM') == {'start': 1255, 'end': 1345}
	assert find_time('1255-0150PM') == {'start': 1255, 'end': 1350}
	assert find_time('1255-0155PM') == {'start': 1255, 'end': 1355}
	assert find_time('1255-0200PM') == {'start': 1255, 'end': 1400}
	assert find_time('1255-0230PM') == {'start': 1255, 'end': 1430}
	assert find_time('1255-0235PM') == {'start': 1255, 'end': 1435}
	assert find_time('1255-0255PM') == {'start': 1255, 'end': 1455}
	assert find_time('1255-0300PM') == {'start': 1255, 'end': 1500}
	assert find_time('1255-0325PM') == {'start': 1255, 'end': 1525}
	assert find_time('1255-0355PM') == {'start': 1255, 'end': 1555}
	assert find_time('1255-0500PM') == {'start': 1255, 'end': 1700}
	assert find_time('1255-1350PM') == {'start': 1255, 'end': 1350}
	assert find_time('1255-1355PM') == {'start': 1255, 'end': 1355}
	assert find_time('1255-1555PM') == {'start': 1255, 'end': 1555}

	assert find_time('1:00-3:00PM') == {'start': 1300, 'end': 1500}
	assert find_time('8:00-9:25') == {'start': 800, 'end': 925}
