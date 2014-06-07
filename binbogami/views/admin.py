import os, shutil
from re import match
from flask import Blueprint, g, session, render_template, abort, request, redirect
from flask import url_for, current_app, Markup
from werkzeug.utils import secure_filename
from binbogami.views.register import hash_password
from mutagenx.mp3 import MP3
from mutagenx.oggvorbis import OggVorbis
from mutagenx.oggopus import OggOpus
from mutagenx.oggspeex import OggSpeex
from PIL import Image
from binbogami.views.register import check_email

admin = Blueprint("admin", __name__, template_folder="templates")

#itunes_categories = ["Arts", "Design", "Fashion &amp; Beauty", "Food",
#                     "Literature", "Performing Arts", "Visual Arts",
#                     "Business", "Business News", "Careers", "Investing",
#                     "Management &amp; Marketing", "Shopping", "Comedy",
#                     "Education", "Education Technology", "Higher Education",
#                     "K-12", "Language Courses", "Training", "Games &amp; Hobbies",
#                     "Automotive", "Aviation", "Hobbies", "Other Games",
#                     "Video Games", "Government &amp; Organizations", "Local",
#                     "National", "Non-Profit", "Regional", "Health",
#                     "Alternative Health", "Fitness &amp; Nutrition", "Self-Help",
#                     "Sexuality", "Kids &amp; Family", "Music", "News &amp; Politics",
#                     "Region &amp; Spirituality", "Buddhism", "Christianity",
#                     "Hinduism", "Islam", "Judaism", "Spirituality",
#                     "Science &amp; Medicine", "Medicine", "Natural Sciences",
#                     "Social Sciences", "Society &amp; Culture", "History",
#                     "Personal Journals", "Philosophy", "Places &amp; Travel",
#                     "Sports &amp; Recreation", "Amateur", "College &amp; High School",
#                     "Outdoor", "Professsional", "Technology", "Gadgets", "Tech News",
#                     "Podcasting", "Software How-To", "TV &amp; Film"]

itunes_categories = [
    "Arts", "Business", "Comedy", "Education", "Games & Hobbies",
    "Government & Organizations", "Health", "Kids & Family", "Music",
    "News & Politics", "Religion & Spirituality", "Science & Medicine",
    "Society & Culture", "Sports & Recreation", "Technology", "TV & Film"
]

@admin.route("/admin")
def show_casts():
    if 'username' in session:
        casts = g.sqlite_db.execute("select name, description, url, image, id from podcasts_header where owner=(?)",
                                    session['uid'])
        rows = casts.fetchall()
        cast_list = None
        if rows != []:
            cast_list = []
            for items in rows:
                imgurlsplit = items[3].rsplit("/")
                imgurl = imgurlsplit[len(imgurlsplit)-1]
                cast_list.append((items[0], items[1], items[2], imgurl))
        return render_template("podcast_admin.html", list=cast_list,
                                nocast="No casts.", friendly_name=session['name'])
    else:
        #TODO: implement this in a prettier manner.
        abort(401)

@admin.route("/admin/<castname>")
def show_eps(castname):
    if 'username' in session:
        podcastid = get_id("id, name", castname, session['uid'])
        if podcastid != None:
            eps = g.sqlite_db.execute(
                "select title, description, castfile, filetype from podcasts_casts where podcast=(?) order by date desc",
                [podcastid[0]]
            ).fetchall()
            list_template = []
            if eps != []:
                for ep in eps:
                    cast_url = url_for("serve.serve_file", castname=podcastid[1],
                                        epname=ep[0]) + "." + ep[3]
                    list_template.append((ep[0], ep[1], cast_url))
            return render_template(
                "ep_admin.html", podcastid=podcastid, list=list_template,
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
            return render_template("podcasts_new.html", itunes_categories=itunes_categories)
        elif request.method == "POST":
            #only one podcast for each name on the server; owner doesn't matter
            query = g.sqlite_db.execute("select name from podcasts_header where name=(?)",
                                [request.form['castname']]
            )
            result = query.fetchone()
            #.fetchone() returns None where no results are found; .fetchall() an empty list.
            if result == None:
                if validate_url(request.form['url']) == 1:
                    return render_template("podcasts_new.html", error="You did not supply a valid URL.",
                                            itunes_categories=itunes_categories)
                img = request.files['img']
                if len(img.filename) != 0:
                    img_upload = image_upload(img, None, "new")
                    if img_upload == 0:
                        return redirect(url_for('admin.show_casts'))
                    elif img_upload == 1:
                        error = "Incorrect image size."
                    else:
                        error = "Your image must be a JPEG, GIF or PNG."
                else:
                    error = "You did not select an image to upload."
                return render_template("podcasts_new.html", error=error, itunes_categories=itunes_categories)
            else:
                error = "You already have a podcast by that name."
                return render_template("podcasts_new.html", error=error, itunes_categories=itunes_categories)
    else:
        #TODO: implement this in a prettier manner.
        abort(401)

@admin.route("/admin/edit/<castname>", methods=['GET', 'POST'])
def edit_cast(castname):
    if 'username' in session:
        podcastid = get_id("id, name, image", castname, session['uid'])
        if request.method == "GET":
            if podcastid != None:
                cast_details = get_id("id, owner, name, description, url, image, categories", castname, session['uid'])
                cast_img_list = cast_details[5].rsplit("/")
                cast_img = cast_img_list[len(cast_img_list)-1]
                cast_img_url = request.url_root + "image/" + cast_img
                return render_template(
                    "podcasts_edit.html", cast_details=cast_details,
                    cast_img_url=cast_img_url, itunes_categories=itunes_categories
                    )
            else:
                abort(401)
        elif request.method == "POST":
            if podcastid != None:
                cast_details = get_id("id, owner, name, description, url, image, categories", castname, session['uid'])
                cast_img_list = cast_details[5].rsplit("/")
                cast_img = cast_img_list[len(cast_img_list)-1]
                cast_img_url = request.url_root + "image/" + cast_img
                if validate_url(request.form['url']) == 1:
                    return render_template("podcasts_edit.html", error="You did not supply a valid URL.",
                                            itunes_categories=itunes_categories,
                                            cast_details=cast_details,
                                            cast_img_url=cast_img_url)
                if request.form['castname'] != podcastid[1]:
                    episodes = g.sqlite_db.execute(
                        "select id, title, castfile, filetype from podcasts_casts where podcast=(?)",
                        [podcastid[0]]
                    ).fetchall()
                    if len(episodes) != 0:
                        new_folder = False
                        for episode in episodes:
                            secure_podcast_name = secure_filename(request.form['castname'])
                            secure_ep_name = secure_filename(episode[1])
                            secure_file_ext = secure_filename(episode[3])
                            new_filename = secure_podcast_name + "/" + secure_ep_name + "." + secure_file_ext
                            filepath = os.path.join(
                                current_app.config['UPLOAD_FOLDER'],
                                new_filename
                            )
                            if not os.path.isdir(os.path.join(current_app.config["UPLOAD_FOLDER"], secure_podcast_name)):
                                os.mkdir(os.path.join(current_app.config["UPLOAD_FOLDER"], secure_podcast_name))
                                new_folder = True
                            os.rename(episode[2], filepath)
                            g.sqlite_db.execute(
                                "update podcasts_casts set castfile=(?) where id=(?)",
                                [filepath, episode[0]]
                            )
                            g.sqlite_db.commit()
                        if new_folder == True:
                            os.rmdir(os.path.join(current_app.config["UPLOAD_FOLDER"], secure_filename(cast_details[2])))
                img = request.files['img']
                if len(img.filename) != 0:
                    img_upload = image_upload(img, podcastid, "edit")
                    if img_upload == 0:
                        return redirect(url_for('admin.show_casts'))
                    elif img_upload == 1:
                        return "Image incorrect size."
                    else:
                        return "Image incorrect format."
                else:
                    g.sqlite_db.execute(
                        "update podcasts_header set name=(?), description=(?), url=(?), categories=(?) where id=(?)",
                        [request.form['castname'], Markup(request.form['description']).striptags(),
                        request.form['url'], request.form['category'], podcastid[0]]
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
            if podcastid != None:
                return render_template("ep_new.html", podcastid=podcastid)
            else:
                return "This cast does not exist, or you do not own it."
        elif request.method == "POST":
            if podcastid != None:
                ep = request.form["file-upload"]
                query = g.sqlite_db.execute(
                    "select title from podcasts_casts where title=(?) and podcast=(?)",
                    [request.form['epname'], podcastid[0]]
                )
                result = query.fetchone()
                if ep and result == None and len(ep) != 0:
                    cast_upload(
                        ep, podcastid, request.form["epname"], request.form['description'], "new"
                    )
                    return redirect(url_for('admin.show_eps', castname=castname))
                else:
                    return "Error."
            else:
                return "Not your podcast."
    else:
        abort(401)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ["mp3", "ogg", "opus", "spx"]

def cast_upload(ep_file, podcast, ep_name, ep_description, neworedit):
    file_ext = ep_file.rsplit('.', 1)[1]
    secure_podcast_name = secure_filename(podcast[1])
    secure_ep_name = secure_filename(ep_name)
    secure_file_ext = secure_filename(file_ext)
    new_filename = secure_podcast_name + "/" + secure_ep_name + "." + secure_file_ext
    filepath = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                new_filename
                )
    if not os.path.isdir(os.path.join(current_app.config["UPLOAD_FOLDER"], secure_podcast_name)):
        os.mkdir(os.path.join(current_app.config["UPLOAD_FOLDER"], secure_podcast_name))
    try:
        shutil.move(os.path.join(current_app.config["UPLOAD_FOLDER"], "tmp", ep_file), filepath)
    except:
        return "Something bad happened."
    if file_ext == "mp3":
        file_length = MP3(filepath).info.length
    elif file_ext == "ogg":
        file_length = OggVorbis(filepath).info.length
    elif file_ext == "spx":
        file_length = OggSpeex(filepath).info.length
    elif file_ext == "opus":
        file_length = OggOpus(filepath).info.length
    else:
        return "This shouldn't happen"

    if neworedit == "new":
        g.sqlite_db.execute(
            "insert into podcasts_casts (podcast, title, description, castfile, date, length, filetype) values (?,?,?,?, datetime('now'),?,?)",
            [
                podcast[0], ep_name,
                ep_description, filepath,
                file_length, file_ext
            ]
        )
        g.sqlite_db.commit()
    else:
        g.sqlite_db.execute(
            "update podcasts_casts set castfile=(?), length=(?), filetype=(?) where title=(?)",
            [filepath, file_length, file_ext, ep_name])
        g.sqlite_db.commit()

def image_upload(img, meta_array, neworedit):
    PIL_img = Image.open(img)
    if img.filename.rsplit(".", 1)[1] in ["jpg", "jpeg", "gif", "png"]:
        if PIL_img.size[0] == 1400 and PIL_img.size[1] == 1400:
            filename = request.form['castname'] + "." + \
                img.filename.rsplit(".", 1)[1]
            safe_filename = secure_filename(filename)
            imgpath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"],
                    safe_filename
            )
            # opening the request.files object (Werkzeug FileStorage) with PIL
            # does "something" to it - won't save from that function. Works
            # with PIL, though.
            try:
                PIL_img.save(imgpath)
            except:
                return 3
            if neworedit == "edit":
                try:
                    os.remove(meta_array[2])
                except FileNotFoundError:
                    pass
                g.sqlite_db.execute(
                    "update podcasts_header set name=(?), description=(?), url=(?), image=(?), categories=(?) where id=(?)",
                    [request.form['castname'], request.form['description'],
                    request.form['url'], imgpath, request.form['category'], meta_array[0]]
                )
                g.sqlite_db.commit()
            elif neworedit == "new":
                g.sqlite_db.execute(
                    "insert into podcasts_header (owner, name, description, url, image, categories) values (?,?,?,?,?,?)",
                    [session['uid'],request.form['castname'],
                    Markup(request.form['description']).striptags(), request.form['url'],
                    imgpath, request.form['category']]
                )
                g.sqlite_db.commit()
            else:
                return "This should not happen."
            return 0
        else:
            return 1
    else:
        return 2

@admin.route("/admin/edit/<castname>/<epname>", methods=["POST", "GET"])
def edit_ep(castname,epname):
    if 'username' in session:
        podcastid = get_id("id, name, owner", castname, session['uid'])
        cast = g.sqlite_db.execute(
            "select id, podcast, title, description, castfile, filetype from podcasts_casts where title=(?)",
            [epname]
        ).fetchone()
        if request.method == "GET":
            if cast != None:
                return render_template("ep_edit.html", podcastid=podcastid, cast=cast)
            else:
                return "No such episode."
        if request.method == "POST":
            if podcastid != None:
                ep = request.form['file-upload']
                cast_name_check = g.sqlite_db.execute(
                    "select id from podcasts_casts where title=(?)",
                    [request.form['epname']]
                ).fetchone()
                if cast_name_check == None or (cast_name_check != None \
                and request.form['epname'] == cast[2]):
                    if len(ep) == 0:
                        secure_cast_name = secure_filename(castname)
                        secure_episode_name = secure_filename(request.form['epname'])
                        secure_file_ext = secure_filename(cast[5])

                        filepath = os.path.join(
                            current_app.config["UPLOAD_FOLDER"],
                            secure_cast_name, secure_episode_name + "." +
                            secure_file_ext
                        )
                        os.rename(cast[4], filepath)
                        g.sqlite_db.execute(
                            "update podcasts_casts set castfile=(?) where id=(?)",
                            [filepath, cast[0]]
                        )
                        g.sqlite_db.commit()
                    else:
                        try:
                            os.remove(cast[4])
                        except FileNotFoundError:
                            pass
                        cast_upload(ep, podcastid, request.form['epname'], request.form['description'], "edit")
                    g.sqlite_db.execute(
                        "update podcasts_casts set title=(?), description=(?) where id=(?)",
                        [request.form['epname'], request.form['description'], cast[0]]
                    )
                    g.sqlite_db.commit()
                    return "Success."
                else:
                    return "Already have a podcast by that name."
    else:
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

def validate_url(url):
    regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    is_it_a_url = match(regex, url)
    if is_it_a_url == None:
        return 1
    else:
        return 0

@admin.route("/admin/user", methods=["GET", "POST"])
def user_admin():
    #FIXME: As it is, we could register with one email address then change it
    #       to an existing registration, don't think I care enough to fix.
    if 'username' in session:
        user = g.sqlite_db.execute(
            "select username, name, email from users where id=(?)",
            [session['uid']]
        ).fetchone()
        if request.method == "GET":
            return render_template("user_admin.html", user=user)
        else:
            error = None
            if check_email(request.form['email']):
                if len(request.form['password']) == 0:
                    g.sqlite_db.execute(
                        "update users set username=(?), name=(?), email=(?) where id=(?)",
                        [request.form['username'], request.form['name'],
                        request.form['email'], session['uid']]
                    )
                else:
                    password = hash_password(request.form['password'])
                    g.sqlite_db.execute(
                        "update users set username=(?), name=(?), pwhash=(?), email=(?) where id=(?)",
                        [request.form['username'], request.form['name'], password,
                        request.form['email'], session['uid']]
                    )
                g.sqlite_db.commit()
            else:
                error = "Not a valid email address."
            #Call the database again to update the array that is passed to the
            #template
            user = g.sqlite_db.execute(
                "select username, name, email from users where id=(?)",
                [session['uid']]
            ).fetchone()
            return render_template("user_admin.html", user=user, error=error)
    else:
        abort(401)
