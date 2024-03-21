import unittest
from framework.logger import get_logger


class TestServiceProvider(unittest.TestCase):
    def test_get_logger(self):
        logger = get_logger(__name__)
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, __name__)
