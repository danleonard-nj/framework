
import uuid
from datetime import datetime

from framework.logger.providers import get_logger
from framework.serialization import Serializable
from quart import Quart

logger = get_logger(__name__)


def default(obj):
    if isinstance(obj, Serializable):
        return obj.to_dict()
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)

    return str(obj)


def configure_serializer(app: Quart):
    app.json.default = default
    app.json.sort_keys = False
