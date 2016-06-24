import os


def delete_file(path):
    os.remove(path)
    if not quiet:
        print('Deleted', path)
