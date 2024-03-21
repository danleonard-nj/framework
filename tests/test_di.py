import unittest
from uuid import uuid4

from framework.di import service_collection
from framework.di.service_provider import ServiceCollection, ServiceProvider


class MockConfiguration:
    def __init__(self) -> None:
        self.instance_id = str(uuid4())


class MockNestedDependency:
    def __init__(
        self,
        configuration: MockConfiguration
    ):
        self.instance_id = str(uuid4())
        self.configuration = configuration


class MockDependency:
    def __init__(self):
        self.instance_id = str(uuid4())


service_collection = ServiceCollection()
service_collection.add_singleton(MockDependency)


class TestServiceProvider(unittest.TestCase):
    def test_resolve_transient(self):
        # Arrange
        service_collection = ServiceCollection()
        service_collection.add_transient(MockDependency)
        service_provider = ServiceProvider(service_collection)
        service_provider.build()

        # Act
        dependency = service_provider.resolve(MockDependency)
        first_dependency_id = dependency.instance_id

        dependency = service_provider.resolve(MockDependency)
        second_dependency_id = dependency.instance_id

        # Assert
        self.assertNotEqual(first_dependency_id, second_dependency_id)

    def test_resolve_singleton(self):
        # Arrange
        service_collection = ServiceCollection()

        service_collection.add_singleton(MockDependency)

        service_provider = ServiceProvider(service_collection)
        service_provider.build()

        # Act
        first_dependency = service_provider.resolve(MockDependency)
        first_dependency_id = first_dependency.instance_id

        second_dependency = service_provider.resolve(MockDependency)
        second_dependency_id = second_dependency.instance_id

        # Assert
        self.assertEqual(first_dependency_id, second_dependency_id)

    def test_resolve_singleton_nested_dependency(self):
        # Arrange
        service_collection = ServiceCollection()

        service_collection.add_singleton(MockConfiguration)
        service_collection.add_singleton(MockNestedDependency)

        service_provider = ServiceProvider(service_collection)
        service_provider.build()

        # Act
        first_dependency = service_provider.resolve(MockNestedDependency)
        first_dependency_id = first_dependency.instance_id

        second_dependency = service_provider.resolve(MockNestedDependency)
        second_dependency_id = second_dependency.instance_id

        # Assert
        self.assertEqual(first_dependency_id, second_dependency_id)
        self.assertIsNotNone(first_dependency.configuration)
        self.assertIsNotNone(second_dependency.configuration)
        self.assertEqual(first_dependency.configuration.instance_id,
                         second_dependency.configuration.instance_id)
