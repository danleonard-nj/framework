from framework.abstractions.abstract_blueprint import AbstractBlueprint
from framework.logger.providers import get_logger

logger = get_logger(__name__)

health_bp = AbstractBlueprint('health_bp', __name__)


@health_bp.route('/api/health/alive')
def alive(contaier=None):
    return {'status': 'ok'}, 200


@health_bp.route('/api/health/ready')
def ready(container=None):
    return {'status': 'ok'}, 200
