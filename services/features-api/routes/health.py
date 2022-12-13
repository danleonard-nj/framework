from framework.logger.providers import get_logger
from quart import Blueprint

logger = get_logger(__name__)

health_bp = Blueprint('health_bp', __name__)


@health_bp.route('/api/health/alive')
async def alive():
    return {'status': 'ok'}, 200


@health_bp.route('/api/health/ready')
async def ready():
    return {'status': 'ok'}, 200
