"""
Test for views/log.py
"""
from binbogami.tests.test_binbogami import TestBinbogami
import unittest

class TestLog(unittest.TestCase):
    """
    Class for testing views/log.py
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

    def login(self, username, password):
        """
        Helper function for login tests
        """
        return self.app.post('/login', data={
            "username": username,
            "password": password
            }, follow_redirects=True)

    def logout(self):
        """
        Helper function for logout tests
        """
        return self.app.get('/logout', follow_redirects=True)

    def testlogin(self):
        """
        Test login
        """
        rv1 = self.login('admin', 'test')
        assert "List of podcasts for" in rv1.data.decode("utf-8")

    def test_login_incorrect_username(self):
        """
        Test login with an invalid username
        """
        rv2 = self.login('adin', "test")
        assert "Incorrect" in rv2.data.decode("utf-8")

    def test_login_incorrect_password(self):
        """
        Test login with an incorrect password
        """
        rv1 = self.login('admin', 'uddin')
        assert "Incorrect" in rv1.data.decode("utf-8")

    def testlogout(self):
        """
        Test logout
        """
        rv1 = self.login('admin', 'test')
        assert "List of podcasts for" in rv1.data.decode("utf-8")
        rv2 = self.logout()
        assert "marketing: we would rather not mislead" in rv2.data.decode("utf-8")

if __name__ == "__main__":
    unittest.main()

