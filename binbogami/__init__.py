import sqlite3
from flask import Flask, g
from binbogami.views.frontpage import *
from binbogami.views.register import *
from binbogami.views.log import *
from binbogami.views.admin import *
from binbogami.views.serve import *

bbgapp = Flask(__name__)
bbgapp.config.from_object(__name__)

bbgapp.config.update(dict(
    DATABASE="bbg.db",
    DEBUG=True,
    SECRET_KEY="DEVELOPMENTKEY",
    #CHANGE THIS IN PRODUCTION
    UPLOAD_FOLDER="/Users/alexander/git/binbogami/files/"
))


def connect_db():
    db = sqlite3.connect(bbgapp.config['DATABASE'])
    return db


@bbgapp.before_request
def before_request():
    g.sqlite_db = connect_db()


def get_db():
    if not hasattr(g, "sqlite_db"):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@bbgapp.teardown_appcontext
def close_db(error):
    if hasattr(g, "sqlite_db"):
        g.sqlite_db.close()


def init_db():
    with bbgapp.app_context():
        db = get_db()
        with bbgapp.open_resource('schema.sql', mode='r') as f:
            try:
                db.cursor().executescript(f.read())
            except sqlite3.OperationalError as e:
                print("{!r}".format(e))
        db.commit()
        
@bbgapp.errorhandler(401)
def error_401(e):
    return render_template('401.html'), 401

bbgapp.register_blueprint(frontpage)
bbgapp.register_blueprint(register)
bbgapp.register_blueprint(log)
bbgapp.register_blueprint(admin)
bbgapp.register_blueprint(serve)