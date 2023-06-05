def flatten(iter):
    # from http://stackoverflow.com/a/2158532/2347774
    try:
        for el in iter:
            if isinstance(el, str):
                yield el
            else:
                yield from flatten(el)
    except TypeError:
        # oops, guess it's not iterable after all.
        # better just return it
        yield iter
