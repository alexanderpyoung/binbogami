from binbogami.tests.test_binbogami import TestBinbogami
import flask
import unittest

class TestLog(unittest.TestCase):

    def setUp(self):
        TestBinbogami.setUp(self)

    def populate_db(self):
        TestBinbogami.populate_db(self)

    def tearDown(self):
        TestBinbogami.tearDown(self)

    def login(self, username, password):
        return self.app.post('/login', data={
            "username": username,
            "password": password
            }, follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def testlogin(self):
        rv1 = self.login('admin', 'test')
        assert "List of podcasts for" in rv1.data.decode("utf-8")
        rv2 = self.login('adin', "beep")
        assert "Incorrect" in rv2.data.decode("utf-8")

    def testlogout(self):
        rv = self.login('admin', 'test')
        assert "List of podcasts for" in rv.data.decode("utf-8")
        rv = self.logout()
        assert "marketing: we would rather not mislead" in rv.data.decode("utf-8")

if __name__ == "__main__":
    unittest.main()