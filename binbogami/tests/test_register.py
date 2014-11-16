from binbogami.tests.test_binbogami import TestBinbogami
import unittest


class TestRegister(unittest.TestCase):
    def setUp(self):
        TestBinbogami.setUp(self)

    def populate_db(self):
        TestBinbogami.populate_db(self)

    def tearDown(self):
        TestBinbogami.tearDown(self)

