def get_constants(_type):
    return {
        key: value for key, value
        in _type.__dict__.items()
        if not key.startswith('_')
    }
