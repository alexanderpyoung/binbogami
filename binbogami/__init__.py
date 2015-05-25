import psycopg2
from flask import Flask, g
from binbogami.views.frontpage import *
from binbogami.views.register import *
from binbogami.views.log import *
from binbogami.views.admin import *
from binbogami.views.serve import *
from binbogami.views.upload import *
from binbogami.views.stats import *

bbgapp = Flask(__name__)
bbgapp.config.from_pyfile("bbg.cfg")

def connect_db():
    db = psycopg2.connect(bbgapp.config['DATABASE'])
    return db


@bbgapp.before_request
def before_request():
    g.db = connect_db()
    g.db_cursor = g.db.cursor()
    
def get_db():
    with bbgapp.app_context():
        if not hasattr(g, "db"):
            g.db = connect_db()
        return g.db


def init_db():
    with bbgapp.app_context():
        db = get_db()
        with bbgapp.open_resource('schema.sql', mode='r') as f:
            try:
                db.cursor().execute(f.read())
            except psycopg2.OperationalError as e:
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
bbgapp.register_blueprint(upload)
bbgapp.register_blueprint(stats)
