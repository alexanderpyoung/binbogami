import os
from flask import Blueprint, g, session, render_template, abort, request, redirect
from flask import url_for, current_app
from werkzeug.utils import secure_filename
from mutagenx.mp3 import MP3
from mutagenx.oggvorbis import OggVorbis
from mutagenx.oggopus import OggOpus
from mutagenx.oggspeex import OggSpeex

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
            #only one podcast for each name on the server; owner doesn't matter
            query = g.sqlite_db.execute("select name from podcasts_header where name=(?)",
                                [request.form['castname']]
            )
            result = query.fetchone()
            #.fetchone() returns None where no results are found; .fetchall() an empty list.
            if result == None:
                img = request.files['img']
                if img:
                    if img.filename.rsplit(".", 1)[1] in ["jpg", "jpeg", "gif", "png"]:
                        filename = request.form['castname'] + "." + \
                            img.filename.rsplit(".", 1)[1] 
                        safe_filename = secure_filename(filename)
                        imgpath = os.path.join(
                                current_app.config["UPLOAD_FOLDER"],
                                safe_filename
                        )
                        img.save(imgpath)
                        g.sqlite_db.execute(
                            "insert into podcasts_header (owner, name, description, url, image) values (?,?,?,?,?)", 
                            [session['uid'],request.form['castname'],
                            request.form['description'], request.form['url'], imgpath]
                        )
                        g.sqlite_db.commit()
                    else:
                        return "File not recognised format."
                else:
                    return "No image uploaded."
                return redirect(url_for('admin.show_casts'))
            else:
                error = "You already have a podcast by that name."
                return render_template("podcasts_new.html", error=error)
    else:
        #TODO: implement this in a prettier manner.
        abort(401)
  
@admin.route("/admin/<castname>/edit", methods=['GET', 'POST'])
def edit_cast(castname):
    if 'username' in session:
        podcastid = get_id("id, name", castname, session['uid'])
        if request.method == "GET":
            if podcastid != None:
                cast_details = get_id("id, owner, name, description, url, image", castname, session['uid'])
                cast_img_list = cast_details[5].rsplit("/")
                cast_img = cast_img_list[len(cast_img_list)-1]
                cast_img_url = request.url_root + "image/" + cast_img
                return render_template("podcasts_edit.html", cast_details=cast_details, cast_img_url=cast_img_url)
            else:
                abort(401)
        elif request.method == "POST":
            if podcastid != None:
                img = request.files['img']
                if len(img.filename) != 0:
                    if img.filename.rsplit(".", 1)[1] in ["jpg", "jpeg", "gif", "png"]:
                        filename = request.form['castname'] + "." + \
                            img.filename.rsplit(".", 1)[1] 
                        safe_filename = secure_filename(filename)
                        imgpath = os.path.join(
                                current_app.config["UPLOAD_FOLDER"],
                                safe_filename
                        )
                        img.save(imgpath)
                        g.sqlite_db.execute(
                            "update podcasts_header set name=(?), description=(?), url=(?), image=(?)",
                            [request.form['castname'], request.form['description'],
                            request.form['url'], imgpath]
                        )
                        g.sqlite_db.commit()
                        return redirect(url_for('admin.show_casts'))
                    else:
                        return "Unsupported image filetype."
                else:
                    g.sqlite_db.execute(
                        "update podcasts_header set name=(?), description=(?), url=(?)",
                        [request.form['castname'], request.form['description'],
                        request.form['url']]
                    )
                    g.sqlite_db.commit()
                    return redirect(url_for('admin.show_casts'))
            else:
                abort(401)
        else:
            return "Unsupported method."
    else:
        abort(401)  
        
@admin.route("/admin/delete/<castname>")
def delete_cast(castname):
    if 'username' in session:
        # 1) Does the podcast exist? 2) Does it belong to the logged in user?
        #TODO: Delete coverart.
        podcastid = get_id("id", castname, session['uid'])
        if podcastid != None:
            # Get and delete files
            query = g.sqlite_db.execute(
                "select castfile from podcasts_casts where podcast=(?)",
                [podcastid[0]]
            )
            results = query.fetchall()
            for result in results:
                try:
                    os.remove(result[0])
                except FileNotFoundError:
                    pass
            query = g.sqlite_db.execute(
                "select image from podcasts_header where id=(?)",
                [podcastid[0]]
            )
            results = query.fetchone()
            try:
                os.remove(results[0])
            except FileNotFoundError:
                pass
            #Do the associated database operations
            g.sqlite_db.execute(
                "delete from podcasts_header where name=(?)",
                [castname]
            )
            g.sqlite_db.execute(
                "delete from podcasts_casts where podcast=(?)",
                [podcastid[0]]    
            )
            g.sqlite_db.commit()
            return redirect(url_for('admin.show_casts'))
        else:
            return "Sorry, the podcast you are attempting to delete does not exist."
    else:
        #TODO: implement this in a prettier manner
        abort(401)
        
@admin.route("/admin/<castname>/new", methods=['POST', 'GET'])
def new_ep(castname):
    if 'username' in session:
        podcastid = get_id("id, name, owner", castname, session['uid'])
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
                    file_ext = ep.filename.rsplit('.', 1)[1]
                    new_filename = castname + " - " + request.form['epname'] + "." + file_ext                
                    filename = secure_filename(new_filename) 
                    filepath = os.path.join(
                                current_app.config["UPLOAD_FOLDER"], 
                                filename
                                )
                    ep.save(filepath)
                    if file_ext == "mp3":
                        file_length = MP3(filepath).info.length
                    elif file_ext == "ogg":
                        file_length = OggVorbis(filepath).info.length
                    elif file_ext == "spx":
                        file_length = OggSpeex(filepath).info.length
                    elif file_ext == "opus":
                        file_length = OggOpus(filepath).info.length
                    else:
                        print("no idea what happened here")
                    g.sqlite_db.execute(
                        "insert into podcasts_casts (podcast, title, description, castfile, date, length, filetype) values (?,?,?,?, datetime('now'),?,?)",
                        [
                            podcastid[0], request.form['epname'], 
                            request.form['description'], filepath,
                            file_length, file_ext
                        ]
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
                try:
                    os.remove(ep[0])
                except FileNotFoundError:
                    pass
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