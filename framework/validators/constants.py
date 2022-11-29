from framework.utilities.constants import get_constants


def contains_constant(_type, value):
    constants = get_constants(
        _type=_type)

    return value in constants.values()


def contains_constant_key(_type, value):
    constants = get_constants(
        _type=_type)

    return value in constants.keys()
