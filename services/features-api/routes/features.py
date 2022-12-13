from framework.dependency_injection.provider import inject_container_async
from framework.handlers.response_handler_async import response_handler
from framework.middleware.wrappers.authorization_wrappers_async import api_key
from quart import Blueprint, abort, request

from models.feature import CreateFeatureRequest, SetFeatureRequest
from services.feature_service import FeatureService

feature_bp = Blueprint('feature_bp', __name__)


@feature_bp.route('/api/feature/id/<feature_id>', endpoint='get_feature_by_id')
@response_handler
@api_key(name='default')
@inject_container_async
async def get_feature_by_id(container, feature_id):
    feature_service: FeatureService = container.resolve(FeatureService)

    return await feature_service.get_feature_by_id(
        feature_id=feature_id)


@feature_bp.route('/api/feature/id/<feature_id>', methods=['DELETE'], endpoint='delete_feature_by_id')
@response_handler
@api_key(name='default')
@inject_container_async
async def delete_feature_by_id(container, feature_id):
    feature_service: FeatureService = container.resolve(FeatureService)

    return await feature_service.delete_feature_by_id(
        feature_id=feature_id)


@feature_bp.route('/api/feature/key/<feature_key>', endpoint='get_feature_by_key')
@response_handler
@api_key(name='default')
@inject_container_async
async def get_feature_by_key(container, feature_key):
    feature_service: FeatureService = container.resolve(FeatureService)

    return await feature_service.get_feature_by_key(
        feature_key=feature_key)


@feature_bp.route('/api/feature/name/<feature_name>', endpoint='get_feature_by_name')
@response_handler
@api_key(name='default')
@inject_container_async
async def get_feature_by_name(container, feature_name):
    feature_service: FeatureService = container.resolve(FeatureService)

    return await feature_service.get_feature_by_name(
        feature_name=feature_name)


@feature_bp.route('/api/feature', methods=['POST'], endpoint='create_feature')
@response_handler
@api_key(name='default')
@inject_container_async
async def create_feature(container):
    feature_service: FeatureService = container.resolve(FeatureService)

    content = await request.get_json()
    create_feature = CreateFeatureRequest(
        data=content)

    if not create_feature.validate():
        abort(400)

    return await feature_service.insert_feature(
        request=create_feature)


@feature_bp.route('/api/feature', methods=['GET'], endpoint='get_all')
@response_handler
@api_key(name='default')
@inject_container_async
async def get_all(container):
    feature_service: FeatureService = container.resolve(FeatureService)

    features = await feature_service.get_all()
    return {
        'features': features
    }


@feature_bp.route('/api/feature/evaluate/<feature_key>', endpoint='evaluate_feature')
@response_handler
@api_key(name='default')
@inject_container_async
async def evaluate_feature(container, feature_key):
    feature_service: FeatureService = container.resolve(FeatureService)

    return await feature_service.evaluate_feature(
        feature_key=feature_key)


@feature_bp.route('/api/feature/set/<feature_key>', methods=['POST'], endpoint='set_feature')
@response_handler
@api_key(name='default')
@inject_container_async
async def set_feature(container, feature_key):
    feature_service: FeatureService = container.resolve(FeatureService)

    content = await request.get_json()
    feature_request = SetFeatureRequest(
        data=content)

    if not feature_request.validate():
        abort(400)

    return await feature_service.set_feature(
        feature_key=feature_key,
        request=feature_request)
