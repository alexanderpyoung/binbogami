import unittest
import tempfile
import os
from passlib.hash import bcrypt
import sqlite3
import sys
import binbogami

class TestBinbogami(unittest.TestCase):
    def setUp(self):
        self.db, binbogami.bbgapp.config['DATABASE'] = tempfile.mkstemp()
        binbogami.bbgapp.config['TESTING'] = True
        self.app = binbogami.bbgapp.test_client()
        binbogami.init_db()
        self.populate_db()

    def populate_db(self):
        # if we're actually changing the database outside of the application context, we need to manually set up the db
        # connection.
        pwbytes = 'test'
        hashedpw = bcrypt.encrypt(pwbytes)
        db = sqlite3.connect(binbogami.bbgapp.config['DATABASE'])
        db.execute('insert into users (username, name, pwhash, email) values (?, ?, ?, ?)',
                                    ['admin', 'admin', hashedpw, 'test@email.com'])
        db.commit()

    def tearDown(self):
        os.close(self.db)
        os.unlink(binbogami.bbgapp.config['DATABASE'])

if __name__ == '__main__':
    unittest.main()
