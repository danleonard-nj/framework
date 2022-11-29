from framework.abstractions.abstract_app import AbstractServer
from framework.logger.providers import get_logger

logger = get_logger(__name__)


def allow_any(response):
    logger.info(f'Adding CORS headers to response')
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Method'] = '*'

    logger.info(f'Response headers: {dict(response.headers)}')
    return response


def add_cors_hook(app: AbstractServer, config=None):
    app.after_request_funcs.setdefault(
        None, []).append(
            allow_any)
