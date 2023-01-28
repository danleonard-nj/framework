
import uuid
from datetime import datetime

from quart import Quart

from framework.logger.providers import get_logger
from framework.serialization import Serializable

logger = get_logger(__name__)


def default(obj):
    if isinstance(obj, Serializable):
        return obj.to_dict()
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)

    return str(obj)


def configure_serializer(
    app: Quart
):
    '''
    Use framework-default serialization
    configuration for service responses

    i.e. handle response objects that
    implement `Serializable` by default

    '''

    app.json.default = default
    app.json.sort_keys = False
