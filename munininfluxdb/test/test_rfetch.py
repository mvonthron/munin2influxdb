import unittest

from . import mock


@unittest.skipUnless(mock, "unittest.mock is not available.")
class TestRFetch(unittest.TestCase):

    def test_main(self):
        self.skipTest('This function does not seem to do anything useful!')
