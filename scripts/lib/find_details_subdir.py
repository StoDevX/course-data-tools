def find_details_subdir(clbid):
	str_clbid = str(clbid)
	clbid = str_clbid.zfill(10)

	n_thousand = int(int(clbid) / 1000)
	thousands_subdir = (n_thousand * 1000)

	return str(thousands_subdir).zfill(5) + '/' + str_clbid
