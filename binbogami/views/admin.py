import os
from flask import Blueprint, g, session, render_template, abort, request, redirect
from flask import url_for, current_app
from werkzeug.utils import secure_filename

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
        
@admin.route("/admin/<castname>")
def show_eps(castname):
    if 'username' in session:
        podcastid = get_id("id, name", castname, session['uid'])
        if podcastid != None:
            eps = g.sqlite_db.execute(
                "select title, description, castfile from podcasts_casts where podcast=(?)",
                [podcastid[0]]
            ).fetchall()
            list = None
            if eps != []:
                list = eps
            return render_template(
                "ep_admin.html", podcastid=podcastid, list=list, 
                noep="No episodes.", castname=castname
            )
        else:
            return "You don't own this podcast."
    else:
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
            #.fetchone() returns None where no results are found; .fetchall() an empty list.
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
        
@admin.route("/admin/<castname>/new", methods=['POST', 'GET'])
def new_ep(castname):
    if 'username' in session:
        podcastid = get_id("id, name", castname, session['uid'])
        if request.method == "GET":
            return render_template("ep_new.html", podcastid=podcastid)
        elif request.method == "POST":
            if podcastid != None:
                ep = request.files['castfile']
                query = g.sqlite_db.execute(
                    "select title from podcasts_casts where title=(?) and podcast=(?)",
                    [request.form['epname'], podcastid[0]]
                )
                result = query.fetchone()
                if ep and allowed_file(ep.filename) and result == None:
                    new_filename = request.form['epname'] + "." + \
                                                ep.filename.rsplit('.', 1)[1]
                    filename = secure_filename(new_filename) 
                    filepath = os.path.join(
                                current_app.config["UPLOAD_FOLDER"], 
                                filename
                                )
                    ep.save(filepath)
                    g.sqlite_db.execute(
                        "insert into podcasts_casts (podcast, title, description, castfile) values (?,?,?,?)",
                        [podcastid[0], request.form['epname'], request.form['description'], filepath]
                    )
                    g.sqlite_db.commit()
                
                    return "Success."
                elif not allowed_file(ep.filename):
                    return "File type not allowed."
                elif result != None:
                    return "Cast already exists."
            else:
                return "Not your podcast."
    else:
        abort(401)
        
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ["mp3", "ogg", "opus", "spx"]

@admin.route("/admin/delete/<castname>")
def delete_cast(castname):
    if 'username' in session:
        # 1) Does the podcast exist? 2) Does it belong to the logged in user?
        podcastid = get_id("id", castname, session['uid'])
        if podcastid != None:
            # Get and delete files
            query = g.sqlite_db.execute(
                "select castfile from podcasts_casts where podcast=(?)",
                [podcastid[0]]
            )
            results = query.fetchall()
            for result in results:
                os.remove(result[0])
            #Do the associated database operations
            g.sqlite_db.execute(
                "delete from podcasts_header where name=(?)",
                [castname]
            )
            g.sqlite_db.execute(
                "delete from podcasts_casts where podcast=(?)",
                [str(podcastid)]    
            )
            g.sqlite_db.commit()
            return redirect(url_for('admin.show_casts'))
        else:
            return "Sorry, the podcast you are attempting to delete does not exist."
    else:
        #TODO: implement this in a prettier manner
        abort(401)
        
@admin.route("/admin/delete/<castname>/<epname>")
def delete_ep(castname, epname):
    if 'username' in session:
        # 1) Does the episode exist? 2) Does it belong to the logged in user?
        podcastid = get_id("id", castname, session['uid'])
        episode = g.sqlite_db.execute(
            "select castfile from podcasts_casts where podcast=(?) and title=(?)",
            [podcastid[0], epname]
        ).fetchall()
        if podcastid != None and episode != []:
            # Get and delete file
            for ep in episode:
                os.remove(ep[0])
            #Do the associated database operations
            g.sqlite_db.execute(
                "delete from podcasts_casts where podcast=(?) and title=(?)",
                [podcastid[0], epname]    
            )
            g.sqlite_db.commit()
            return redirect(url_for('admin.show_casts'))
        else:
            return "Sorry, the podcast you are attempting to delete does not exist."
    else:
        #TODO: implement this in a prettier manner
        abort(401)
        
def get_id(query, castname, owner):
    getid = g.sqlite_db.execute(
        "select " + query +" from podcasts_header where name=(?) and owner=(?)", 
        [castname, owner]
    )
    return getid.fetchone()