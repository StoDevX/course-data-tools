def get_all_keys(list_of_objects):
    return sorted(set([key for obj in list_of_objects for key in obj.keys()]))
