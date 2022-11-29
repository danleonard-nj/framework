

from unittest.mock import Mock


class MockResponse:
    def __init__(self, status_code, json):
        self.status_code = status_code
        self._json = json

    def json(self):
        return self._json


class MockContainer:
    def __init__(self):
        self.returns = {}

    def define(self, _type, obj):
        self.returns[_type] = obj

    def resolve(self, _type):
        return self.returns.get(_type) or Mock()
