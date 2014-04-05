from flask import Blueprint, g, session, render_template, abort, request, redirect
from flask import url_for

admin = Blueprint("admin", __name__, template_folder="templates")

@admin.route("/admin")
def show_casts():
    if 'username' in session:
        casts = g.sqlite_db.execute("select name, description, url, image, id from podcasts_header where owner=(?)",
                                    session['uid'])
        rows = casts.fetchall()
        list = None
        if rows != []:
            list = rows
        return render_template("podcast_admin.html", list=list, nocast="No casts.")
    else:
        #TODO: implement this in a prettier manner.
        abort(401)

@admin.route("/admin/new/cast", methods=['POST', 'GET'])
def new_cast():
    if 'username' in session:    
        if request.method == "GET":
            return render_template("podcasts_new.html")
        elif request.method == "POST":
            query = g.sqlite_db.execute("select name from podcasts_header where name=(?) and owner=(?)",
                                [request.form['castname'], session['uid']]
            )
            result = query.fetchone()
            if result == None:
                g.sqlite_db.execute(
                    "insert into podcasts_header (owner, name, description, url, image) values (?,?,?,?,?)", 
                    [session['uid'],request.form['castname'],
                    request.form['description'], request.form['url'], request.form['img']]
                    )
                g.sqlite_db.commit()
                return redirect(url_for('admin.show_casts'))
            else:
                error = "You already have a podcast by that name."
                return render_template("podcasts_new.html", error=error)
    else:
        #TODO: implement this in a prettier manner.
        abort(401)

@admin.route("/admin/delete/cast/<castname>")
def delete_cast(castname):
    if 'username' in session:
        # 1) Does the podcast exist? 2) Does it belong to the logged in user?
        getid = g.sqlite_db.execute(
            "select id from podcasts_header where name=(?) and owner=(?)", 
            [castname, session['uid']]
        )
        podcastid = getid.fetchone()
        if podcastid != None:
            g.sqlite_db.execute(
                "delete from podcasts_header where name=(?)",
                [castname]
            )
            g.sqlite_db.execute(
                "delete from podcasts_casts where podcast=(?)",
                [str(podcastid)]    
            )
            g.sqlite_db.commit()
            #TODO: Add logic around deleting files.
            return redirect(url_for('admin.show_casts'))
        else:
            return "Sorry, the podcast you are attempting to delete does not exist."
    else:
        #TODO: implement this in a prettier manner
        abort(401)
    