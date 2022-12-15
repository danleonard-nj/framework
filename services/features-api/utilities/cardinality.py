from framework.crypto.hashing import sha256
import json


def get_cardinality_key(
    feature_key,
    feature_type,
    name,
    description,
    value
):
    return sha256(
        data=json.dumps([
            feature_key,
            feature_type,
            name,
            description,
            value
        ])
    )
