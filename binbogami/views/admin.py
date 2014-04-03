from flask import Blueprint, g, session, render_template, abort

admin = Blueprint("admin", __name__, template_folder="templates")

@admin.route("/admin/")
def show_casts():
    if 'username' in session:
        casts = g.sqlite_db.execute("select * from podcasts_header where owner=(?)",
                                    str(session['uid']))
        rows = casts.fetchall()
        castlist = []
        list = None
        if rows != []:
            list = rows
        return render_template("podcast_admin.html", list=list, nocast="No casts.")
    else:
        #TODO: implement this in a prettier manner.
        abort(401)
