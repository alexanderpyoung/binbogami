"""
Helper class for binbogami tests
"""
import unittest
from passlib.hash import bcrypt
import testing.postgresql
import psycopg2
import binbogami

class TestBinbogami(unittest.TestCase):
    """
    helper class for tests
    """
    def setUp(self):
        self.db_entity = testing.postgresql.Postgresql()
        binbogami.bbgapp.config['DATABASE'] = "host=" + self.db_entity.dsn()['host'] + " port=" \
                + str(self.db_entity.dsn()['port']) + " user=" + self.db_entity.dsn()['user'] + \
                " dbname=" + self.db_entity.dsn()['database']
        binbogami.bbgapp.config['TESTING'] = True
        self.app = binbogami.bbgapp.test_client()
        binbogami.init_db()
        self.populate_db()

    def populate_db(self):
        """
        Put some stuff in the DB to test against
        """
        # if we're actually changing the database outside of the application context,
        # we need to manually set up the db connection.
        pwbytes = 'test'
        hashedpw = bcrypt.encrypt(pwbytes)
        db = psycopg2.connect(**self.db_entity.dsn())
        db.cursor().execute('insert into users (username, name, pwhash, email) \
                            values (%s, %s, %s, %s)',
                            ['admin', 'admin', hashedpw, 'test@email.com'])
        db.commit()

    def tearDown(self):
        self.db_entity.stop()

if __name__ == '__main__':
    unittest.main()

