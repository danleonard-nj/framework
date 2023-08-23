from framework.logger import get_logger
from quart import request

from providers.feature_provider import FeatureProvider
from utilities.meta import MetaBlueprint

API_KEY='feature-api'

logger = get_logger(__name__)

feature_bp = MetaBlueprint('feature_bp', __name__)


@feature_bp.with_key_auth('/api/feature/id/<feature_id>', methods=['GET'], key_name=API_KEY)
async def get_feature_by_id(container, feature_id):
    feature_provider: FeatureProvider = container.resolve(FeatureProvider)

    return await feature_provider.get_feature_by_id(
        feature_id=feature_id)


@feature_bp.with_key_auth('/api/feature/id/<feature_id>', methods=['DELETE'], key_name=API_KEY)
async def delete_feature_by_id(container, feature_id):
    feature_provider: FeatureProvider = container.resolve(FeatureProvider)

    return await feature_provider.delete_feature_by_id(
        feature_id=feature_id)


@feature_bp.with_key_auth('/api/feature/key/<feature_key>', methods=['GET'], key_name=API_KEY)
async def get_feature_by_key(container, feature_key):
    feature_provider: FeatureProvider = container.resolve(FeatureProvider)

    return await feature_provider.get_feature_by_key(
        feature_key=feature_key)


@feature_bp.with_key_auth('/api/feature/name/<feature_name>', methods=['GET'], key_name=API_KEY)
async def get_feature_by_name(container, feature_name):
    feature_provider: FeatureProvider = container.resolve(FeatureProvider)

    return await feature_provider.get_feature_by_name(
        feature_name=feature_name)


@feature_bp.with_key_auth('/api/feature', methods=['POST'], key_name=API_KEY)
async def create_feature(container):
    feature_provider: FeatureProvider = container.resolve(FeatureProvider)

    body = await request.get_json()

    return await feature_provider.create_feature(
        body=body)


@feature_bp.with_key_auth('/api/feature', methods=['GET'], key_name=API_KEY)
async def get_all(container):
    feature_provider: FeatureProvider = container.resolve(FeatureProvider)

    return await feature_provider.get_all()


@feature_bp.with_key_auth('/api/feature/evaluate/<feature_key>', methods=['GET'], key_name=API_KEY)
async def get_evaluate_feature(container, feature_key):
    feature_provider: FeatureProvider = container.resolve(FeatureProvider)

    return await feature_provider.evaluate_feature(
        feature_key=feature_key)


@feature_bp.with_key_auth('/api/feature/evaluate/<feature_key>', methods=['PUT'], key_name=API_KEY)
async def evaluate_feature_update(container, feature_key):
    feature_provider: FeatureProvider = container.resolve(FeatureProvider)

    body = await request.get_json()

    return await feature_provider.evaluate_feature_update(
        feature_key=feature_key,
        body=body)


@feature_bp.with_key_auth('/api/feature', methods=['PUT'], key_name=API_KEY)
async def update_feature(container):
    feature_provider: FeatureProvider = container.resolve(FeatureProvider)

    body = await request.get_json()

    return await feature_provider.update_feature(
        body=body)
