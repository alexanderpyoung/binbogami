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

    def register(self, username, password, name, email):
        return self.app.post('/register', data={
            "username": username,
            "password": password,
            "name": name,
            "email": email
            }, follow_redirects=True)

    def test_register_success(self):
        """
        Test registration
        """
        rv1 = self.register('new', 'xxxx', 'test user account', 'a@aa.com')
        assert "Username already in use" not in rv1.data.decode("utf-8")
        assert "Email address already in use" not in rv1.data.decode("utf-8")
        assert "Not a valid email address" not in rv1.data.decode("utf-8")
        assert "test user account" in rv1.data.decode("utf-8")

    def test_register_failure_name(self):
        """
        Test a failure of registration for extant username
        """
        rv1 = self.register('admin', 'xxxx', 'test', 'a@a.com')
        assert "Username already in use" in rv1.data.decode("utf-8")

    def test_register_failure_email_used(self):
        """
        Test for a used email address
        """
        rv1 = self.register('fsdfdsf', 'xxxx', 'test', 'test@email.com')
        assert "Email address already in use" in rv1.data.decode("utf-8")

    def test_register_failure_email_invalid(self):
        """
        Test with an invalid email address
        """
        rv1 = self.register('username2', 'xxxx', 'test', 'fake_email')
        assert "Not a valid email address" in rv1.data.decode("utf8")

if __name__ == "__main__":
    unittest.main()
