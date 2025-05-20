from deprecated import deprecated


@deprecated
def not_none(value, name):
    if (isinstance(value, str) and value == '') or value is None:
        raise Exception(f'{name} cannot be null or empty')


def none_or_whitespace(value):
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ''

    return False
