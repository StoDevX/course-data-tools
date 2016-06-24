from .ensure_dir_exists import ensure_dir_exists


def save_data(data, filepath):
    ensure_dir_exists(filepath)
    with open(filepath, mode='w+', newline='\n') as outfile:
        outfile.write(data)
