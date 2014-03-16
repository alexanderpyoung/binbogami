from flask import Flask
from binbogami.views.frontpage import *

bbgapp = Flask(__name__)

bbgapp.register_blueprint(frontpage)
