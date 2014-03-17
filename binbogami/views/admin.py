from flask import Blueprint, g, session, render_template, abort

admin = Blueprint("admin", __name__, template_folder="templates")

@admin.route("/admin/")
def show_casts():
    if 'username' in session:
        return render_template("podcast_admin.html")
    else:
        #TODO: implement this in a prettier manner.
        abort(401)
