from quart import request
from framework.logger.providers import get_logger

logger = get_logger(__name__)


def preserve_source_context(func):
    if not hasattr(request, 'source_context'):
        request.source_context = []

    logger.info(f'Storing source context: {func}')
    logger.info(f'Stored context: {request.source_context}')
    request.source_context.append(func)
