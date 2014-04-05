from flask import Blueprint, g, session

serve = Blueprint("serve", __name__, template_folder="templates")

@serve.route("/<castname>/<epname>")
def serve_file(castname, epname):
    pass