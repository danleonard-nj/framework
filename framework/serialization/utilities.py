import json

from framework.serialization import Serializable


def serialize(
    obj
):
    if isinstance(obj, Serializable):
        obj = obj.to_dict()

    return json.dumps(obj, indent=True, default=str)
