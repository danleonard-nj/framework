import unittest

from framework.crypto.hashing import md5, sha1, sha256


class TestServiceProvider(unittest.TestCase):
    def test_sha256(self):
        hashed = sha256('test-data')
        value = 'oYYABCL+q4VzKcaE6f6RQSsaXbCEEAs3qYz8lbYqqGc='

        self.assertIsNotNone(hashed)
        self.assertEqual(hashed, value)

    def test_sha1(self):
        hashed = sha1('test-data')
        value = 'cRXpiQ9bXMaRS9+jt8AR2xza/ts='

        self.assertIsNotNone(hashed)
        self.assertEqual(hashed, value)

    def test_md5(self):
        hashed = md5('test-data')
        value = 'JDRuG1AGZgcFmvNuO2hLJA=='

        self.assertIsNotNone(hashed)
        self.assertEqual(hashed, value)
