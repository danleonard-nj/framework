

from unittest.mock import Mock
import unittest

from framework.testing.helpers import (
    inject_test_dependency,
    inject_mock_middleware
)
from framework.clients.feature_client import FeatureClient
from framework.clients.cache_client import CacheClient


class ApiTest(unittest.TestCase):
    def configure(self, app, provider):
        self.app = app
        self.mock_feature_client = Mock()
        self.mock_cache_client = Mock()

        inject_test_dependency(
            provider=provider,
            _type=FeatureClient,
            instance=self.mock_feature_client)
        inject_test_dependency(
            provider=provider,
            _type=CacheClient,
            instance=self.mock_cache_client)

        inject_mock_middleware(
            provider=provider)

    def _get_mock_auth_headers(self):
        return {
            'Authorization': 'Bearer fake',
            'Content-Type': 'application/json'
        }

    def send_request(self, method, endpoint,  headers=None, json=None):
        with self.app.test_client() as client:
            _headers = (headers or {}) | self._get_mock_auth_headers()
            return client.open(
                endpoint,
                method=method,
                headers=_headers,
                json=json)
