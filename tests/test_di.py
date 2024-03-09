import unittest
from unittest.mock import Mock
from framework.di import service_collection

from framework.di.service_provider import (DependencyRegistration, Lifetime,
                                           ServiceCollection, ServiceProvider)
from uuid import uuid4


class MockDependency:
    def __init__(self):
        self.instance_id = str(uuid4())


service_collection = ServiceCollection()
service_collection.add_singleton(MockDependency)


class TestServiceProvider(unittest.TestCase):
    def setUp(self):
        self.mock_service_collection = service_collection
        self.mock_dependency_registration = Mock(spec=DependencyRegistration)
        self.service_provider = ServiceProvider(self.mock_service_collection)

    def test_resolve_transient(self):
        service_collection = ServiceCollection()
        service_collection.add_transient(MockDependency)
        service_provider = ServiceProvider(service_collection)
        service_provider.build()

        dependency = service_provider.resolve(MockDependency)
        first_dependency_id = dependency.instance_id

        dependency = service_provider.resolve(MockDependency)
        second_dependency_id = dependency.instance_id

        self.assertNotEqual(first_dependency_id, second_dependency_id)

    def test_resolve_singleton(self):
        service_collection = ServiceCollection()
        service_collection.add_singleton(MockDependency)
        service_provider = ServiceProvider(service_collection)
        service_provider.build()

        dependency = service_provider.resolve(MockDependency)
        first_dependency_id = dependency.instance_id

        dependency = service_provider.resolve(MockDependency)
        second_dependency_id = dependency.instance_id

        self.assertEqual(first_dependency_id, second_dependency_id)
