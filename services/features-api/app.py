from framework.abstractions.abstract_request import RequestContextProvider
from framework.dependency_injection.provider import InternalProvider
from framework.logger.providers import get_logger
from framework.serialization.serializer import configure_serializer
from quart import Quart

from routes.features import feature_bp
from routes.health import health_bp
from utilities.provider import ContainerProvider

logger = get_logger(__name__)
app = Quart(__name__)


app.register_blueprint(health_bp)
app.register_blueprint(feature_bp)

ContainerProvider.initialize_provider()
InternalProvider.bind(ContainerProvider.get_service_provider())


@app.before_serving
async def startup():
    RequestContextProvider.initialize_provider(
        app=app)


@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response


configure_serializer(app)


if __name__ == '__main__':
    app.run(debug=True, port='5086')
