"""
Module with testcases for Book
"""
# pylint: disable=missing-function-docstring
from unittest import TestCase
from QibLibrary.session import Session


class SessionTest(TestCase):
    """
    Testcase for Session
    """
    def testDefaultReturnIsNone(self):
        s = Session()

        with self.subTest(f"Checking return on 'aKeyThatDoesNotExist'"):
            self.assertIsNone(s.aKeyThatDoesNotExist)


    def testSetAndGet(self):
        s = Session()
        _value = "aValue"

        with self.subTest(f"Setting 'keyThatHoldsData' to '{_value}' and verifying it"):
            s.keyThatHoldsData = _value
            self.assertEqual(s.keyThatHoldsData, _value)
