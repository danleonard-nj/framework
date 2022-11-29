import json
from deprecated import deprecated


@deprecated
def to_json(obj):
    return json.dumps(obj, indent=True, default=str)


def serialize(obj):
    return json.dumps(obj, indent=True, default=str)
