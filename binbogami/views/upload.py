"""
Binbogami plupload helper module.
"""
from flask import Blueprint, abort, request, current_app
from werkzeug.utils import secure_filename
import os
from binbogami.views.admin import allowed_file

upload = Blueprint("upload", __name__, template_folder="templates")

@upload.route("/upload", methods=["GET", "POST"])
def upload_file():
    """
    Function for handling file uploads.
    """
    if request.method == "POST":
        for dummy_key, file in request.files.items():
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"],
                                        "tmp", filename)
                try:
                    file.save(filepath)
                except:
                    return '{"jsonrpc" : "2.0", "error" : {"code": 500, \
                           "message": "Failed to move uploaded file, please \
                           retry your upload."}, "id" : "id"}'
                return '{"jsonrpc" : "2.0", "result" : null, "id" : "id"}'
            else:
                return '{"jsonrpc" : "2.0", "error" : {"code": 500, "message": \
                       "Filetype not allowed."}, "id" : "id"}'
    else:
        abort(401)
