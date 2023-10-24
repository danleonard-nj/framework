from quart import request
from deprecated import deprecated
from framework.logger.providers import get_logger

logger = get_logger(__name__)


@deprecated
def preserve_source_context(func):
    if not hasattr(request, 'source_context'):
        request.source_context = []

    logger.debug(f'Storing source context: {func}')
    logger.debug(f'Stored context: {request.source_context}')
    request.source_context.append(func)
