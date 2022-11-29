import uuid
from framework.dependency_injection.container import (
    Dependency,
    DependencyType
)
from framework.middleware.authorization import AuthMiddleware
from unittest.mock import Mock


def inject_test_dependency(provider, _type, instance):
    container = provider.get_container()
    container._container[_type] = Dependency(
        _type=_type,
        reg_type=DependencyType.SINGLETON,
        instance=instance)


def inject_mock_middleware(provider):
    auth_middleware = Mock()
    auth_middleware.validate_access_token = Mock(
        return_value=True)

    inject_test_dependency(
        provider=provider,
        _type=AuthMiddleware,
        instance=auth_middleware)


def guid():
    return str(uuid.uuid4())
