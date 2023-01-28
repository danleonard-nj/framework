from utilities.meta import MetaBlueprint
from quart import request

from providers.event_provider import EventProvider

events_bp = MetaBlueprint('events_bp', __name__)


@events_bp.configure('/api/events/evaluate', methods=['POST'], auth_scheme='events')
async def post_update_feature_last_evaluated_date(container):
    event_provider: EventProvider = container.resolve(EventProvider)

    body = await request.get_json()

    return await event_provider.update_feature_last_evaluated_date(
        body=body)
