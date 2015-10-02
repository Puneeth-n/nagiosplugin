from nagiosplugin.platform import with_timeout
import nagiosplugin
import time
import unittest


class PlatformTest(unittest.TestCase):

    def test_timeout(self):
        with self.assertRaises(nagiosplugin.Timeout):
            with_timeout(1, time.sleep, 2)
