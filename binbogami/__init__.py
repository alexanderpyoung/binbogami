"""
Initialisation module for binbogami
"""
import psycopg2
from flask import Flask, g, render_template
from binbogami.views.frontpage import frontpage
from binbogami.views.register import register
from binbogami.views.log import log
from binbogami.views.admin import admin
from binbogami.views.serve import serve
from binbogami.views.upload import upload
from binbogami.views.stats import stats

bbgapp = Flask(__name__)
bbgapp.config.from_pyfile("bbg.cfg")


def connect_db():
    """
    DB connection object creator function
    """
    db = psycopg2.connect(bbgapp.config['DATABASE'])
    return db


@bbgapp.before_request
def before_request():
    """
    before_request function
    """
    g.db = connect_db()
    g.db_cursor = g.db.cursor()


def get_db():
    """
    Function to get db object
    """
    with bbgapp.app_context():
        if not hasattr(g, "db"):
            g.db = connect_db()
        return g.db


def init_db():
    """
    Function to initialise database
    """
    with bbgapp.app_context():
        db = get_db()
        with bbgapp.open_resource('schema.sql', mode='r') as file_resource:
            try:
                db.cursor().execute(file_resource.read())
            except psycopg2.OperationalError as error:
                print("{!r}".format(error))
            db.commit()


@bbgapp.errorhandler(401)
def error_401():
    """
    401 handler
    """
    return render_template('401.html'), 401


bbgapp.register_blueprint(frontpage)
bbgapp.register_blueprint(register)
bbgapp.register_blueprint(log)
bbgapp.register_blueprint(admin)
bbgapp.register_blueprint(serve)
bbgapp.register_blueprint(upload)
bbgapp.register_blueprint(stats)
