
def first(items, func):
    for item in items:
        if func(item):
            return item
