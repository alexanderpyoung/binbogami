"""
tests for views/register.py
"""
from binbogami.tests.test_binbogami import TestBinbogami
import unittest


class TestRegister(unittest.TestCase):
    """
    Class to test registration functionality.
    """

    def setUp(self):
        TestBinbogami.setUp(self)

    def populate_db(self):
        """
        Populate DB
        """
        TestBinbogami.populate_db(self)

    def tearDown(self):
        TestBinbogami.tearDown(self)

