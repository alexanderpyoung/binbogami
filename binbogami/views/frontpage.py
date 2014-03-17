from flask import Blueprint, session, escape

frontpage = Blueprint("frontpage",__name__,
                      template_folder="templates")

@frontpage.route("/")
def index():
    if 'username' in session:
        return "Hello, %s!" % escape(session['name'])
    else:
        return "Hello, world!"
