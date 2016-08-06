def load_data_from_file(filename):
    with open(filename, 'r') as infile:
        return infile.read()
