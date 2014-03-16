from flask import Blueprint

frontpage = Blueprint("frontpage",__name__,
                      template_folder="templates")

@frontpage.route("/")
def index():
    return "Hello, world!"
