from deprecated import deprecated


@deprecated
def select(items, func):
    results = []
    for item in items:
        results.append(func(item))

    return results


@deprecated
def where(items, func):
    results = []
    for item in items:
        if func(item):
            results.append(item)


@deprecated
def first(items, func=None):
    for item in items:
        if func is None:
            return item
        if func(item) is True:
            return item


@deprecated
def any(items, func):
    for item in items:
        if func(item):
            return True
    return False


@deprecated
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
