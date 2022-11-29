from deprecated import deprecated


@deprecated
def not_none(value, name):
    if (isinstance(value, str) and value == '') or value is None:
        raise Exception(f'{name} cannot be null or empty')


def none_or_whitespace(value):
    return value is None or value == ''
