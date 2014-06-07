from flask import Blueprint, abort, request, current_app
from werkzeug.utils import secure_filename
import os
from binbogami.views.admin import allowed_file

upload = Blueprint("upload", __name__, template_folder="templates")

@upload.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        for key, file in request.files.items():
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"],
                                        "tmp", filename)
                file.save(filepath)
            return '{"OK": 0}'
