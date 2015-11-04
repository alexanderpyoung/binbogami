"""
Module for the admin functions of binbogami
"""
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
import random
import string
import smtplib
from email.mime.text import MIMEText

admin = Blueprint("admin", __name__, template_folder="templates")

# itunes_categories = ["Arts", "Design", "Fashion &amp; Beauty", "Food",
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
    """
    Function for core admin page - display user's podcast
    """
    if 'username' in session:
        g.db_cursor.execute("select name, description, url, image, id from \
                             podcasts_header where owner=%s", [session['uid']])
        rows = g.db_cursor.rowcount
        cast_list = None
        if rows is not 0:
            fetch_casts = g.db_cursor.fetchall()
            cast_list = []
            for items in fetch_casts:
                imgurlsplit = items[3].rsplit("/")
                imgurl = imgurlsplit[len(imgurlsplit)-1]
                cast_list.append((items[0], items[1], items[2], imgurl))
        return render_template("podcast_admin.html", list=cast_list,
                               nocast="No casts.", friendly_name=session['name'])
    else:
        abort(401)

@admin.route("/admin/<castname>")
def show_eps(castname):
    """
    Function to show episodes within a podcast
    """
    if 'username' in session:
        podcastid = get_id("id, name", castname, session['uid'])
        if podcastid != None:
            g.db_cursor.execute(
                "select title, description, castfile, filetype from \
                podcasts_casts where podcast=%s order by date desc",
                [podcastid[0]]
            )
            eps = g.db_cursor.rowcount
            list_template = []
            if eps is not 0:
                eps_list = g.db_cursor.fetchall()
                for episode in eps_list:
                    cast_url = url_for("serve.serve_file", castname=podcastid[1],
                                       epname=episode[0]) + "." + episode[3]
                    list_template.append((episode[0], episode[1], cast_url))
            return render_template(
                "ep_admin.html", podcastid=podcastid,
                list=list_template, noep="No episodes.",
                castname=castname
            )
        else:
            return "You don't own this podcast."
    else:
        abort(401)

@admin.route("/admin/new/cast", methods=['POST', 'GET'])
def new_cast():
    """
    Function to handle new podcast creation.
    """
    if 'username' in session:
        if request.method == "GET":
            return render_template("podcasts_new.html", itunes_categories=itunes_categories)
        elif request.method == "POST":
            # only one podcast for each name on the server; owner doesn't matter
            g.db_cursor.execute("select name from podcasts_header where name=%s",
                                [request.form['castname']]
                               )
            result = g.db_cursor.rowcount
            if result is 0:
                if "/" in request.form['castname']:
                    return render_template("podcasts_new.html",
                                           error="No forward slashes permitted \
                                                 in podcast name.",
                                           itunes_categories=itunes_categories)
                if validate_url(request.form['url']) == 1:
                    return render_template("podcasts_new.html",
                                           error="You did not supply a valid URL.",
                                           itunes_categories=itunes_categories)
                if request.form['castname'].strip() == "":
                    return render_template("podcasts_new.html", error="You did \
                                           not supply a valid cast name.",
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
                return render_template("podcasts_new.html", error=error,
                                       itunes_categories=itunes_categories)
            else:
                error = "You already have a podcast by that name."
                return render_template("podcasts_new.html", error=error,
                                       itunes_categories=itunes_categories)
    else:
        abort(401)

@admin.route("/admin/edit/<castname>", methods=['GET', 'POST'])
def edit_cast(castname):
    """
    Function for editing podcasts
    """
    if 'username' in session:
        podcastid = get_id("id, name, image, explicit", castname, session['uid'])
        if request.method == "GET":
            if podcastid != None:
                cast_details = get_id("id, owner, name, description, url, image, \
                                      categories, explicit", castname, session['uid'])
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
                cast_details = get_id("id, owner, name, description, url, image, \
                                      categories, explicit", castname, session['uid'])
                cast_img_list = cast_details[5].rsplit("/")
                cast_img = cast_img_list[len(cast_img_list)-1]
                cast_img_url = request.url_root + "image/" + cast_img
                if "/" in request.form['castname']:
                    return render_template("podcasts_edit.html",
                                           error="No forward slashes permitted in podcast name.",
                                           itunes_categories=itunes_categories,
                                           cast_details=cast_details,
                                           cast_img_url=cast_img_url)
                if request.form['castname'].strip() == "":
                    return render_template("podcasts_edit.html", error="You did not supply \
                                           a valid cast name.", itunes_categories=itunes_categories,
                                           cast_details=cast_details, cast_img_url=cast_img_url)
                if validate_url(request.form['url']) == 1:
                    return render_template("podcasts_edit.html",
                                           error="You did not supply a valid URL.",
                                           itunes_categories=itunes_categories,
                                           cast_details=cast_details,
                                           cast_img_url=cast_img_url)
                if request.form['castname'] != podcastid[1]:
                    g.db_cursor.execute(
                        "select id, title, castfile, filetype from podcasts_casts where podcast=%s",
                        [podcastid[0]]
                    )
                    episode_count = g.db_cursor.rowcount
                    if episode_count is not 0:
                        episodes = g.db_cursor.fetchall()
                        new_folder = False
                        secure_podcast_name = secure_filename(request.form['castname'])
                        if not os.path.isdir(os.path.join(current_app.config["UPLOAD_FOLDER"],
                                                          secure_podcast_name)):
                            os.mkdir(os.path.join(current_app.config["UPLOAD_FOLDER"],
                                                  secure_podcast_name))
                            new_folder = True
                        for episode in episodes:
                            secure_podcast_name = secure_filename(request.form['castname'])
                            secure_ep_name = secure_filename(episode[1])
                            secure_file_ext = secure_filename(episode[3])
                            new_filename = secure_podcast_name + "/" + secure_ep_name \
                                           + "." + secure_file_ext
                            filepath = os.path.join(
                                current_app.config['UPLOAD_FOLDER'],
                                new_filename
                            )
                            os.rename(episode[2], filepath)
                            g.db_cursor.execute(
                                "update podcasts_casts set castfile=%s where id=%s",
                                [filepath, episode[0]]
                            )
                            g.db.commit()
                        if new_folder == True:
                            os.rmdir(os.path.join(current_app.config["UPLOAD_FOLDER"],
                                                  secure_filename(cast_details[2])))
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
                    g.db_cursor.execute(
                        "update podcasts_header set name=%s, description=%s, \
                        url=%s, categories=%s, explicit=%s where id=%s",
                        [request.form['castname'],
                         Markup(request.form['description']).striptags(),
                         request.form['url'], request.form['category'],
                         request.form['explicit'], podcastid[0]]
                    )
                    g.db.commit()
                    return redirect(url_for('admin.show_casts'))
            else:
                abort(401)
        else:
            return "Unsupported method."
    else:
        abort(401)

@admin.route("/admin/delete/<castname>")
def delete_cast(castname):
    """
    Delete cast function.
    """
    if 'username' in session:
        # 1) Does the podcast exist? 2) Does it belong to the logged in user?
        podcastid = get_id("id", castname, session['uid'])
        if podcastid != None:
            # Get and delete files
            g.db_cursor.execute(
                "select castfile from podcasts_casts where podcast=%s",
                [podcastid[0]]
            )
            if g.db_cursor.rowcount is not 0:
                results = g.db_cursor.fetchall()
                for result in results:
                    try:
                        os.remove(result[0])
                    except FileNotFoundError:
                        pass
                g.db_cursor.execute(
                    "select image from podcasts_header where id=%s",
                    [podcastid[0]]
                )
                results = g.db_cursor.fetchone()
                try:
                    os.remove(results[0])
                except FileNotFoundError:
                    pass
                #Do the associated database operations
                g.db_cursor.execute(
                    "delete from podcasts_header where name=%s",
                    [castname]
                )
                g.db_cursor.execute(
                    "delete from podcasts_casts where podcast=%s",
                    [podcastid[0]]
                )
                g.db.commit()
                return redirect(url_for('admin.show_casts'))
            else:
                return "Trying to delete a podcast that doesn't exist."
        else:
            return "Sorry, the podcast you are attempting to delete does not exist."
    else:
        abort(401)

@admin.route("/admin/<castname>/new", methods=['POST', 'GET'])
def new_ep(castname):
    """
    Function to create new podcast episodes
    """
    if 'username' in session:
        podcastid = get_id("id, name, owner", castname, session['uid'])
        if request.method == "GET":
            if podcastid != None:
                return render_template("ep_new.html", podcastid=podcastid)
            else:
                return "This cast does not exist, or you do not own it."
        elif request.method == "POST":
            if podcastid != None:
                if request.form['epname'].strip() == "":
                    return render_template("ep_new.html", podcastid=podcastid,
                                           error="You did not specify a valid podcast name.")
                if "/" in request.form['epname']:
                    return render_template("ep_new.html", podcastid=podcastid,
                                           error="No forward slashes permitted in epsiode name.")
                ep = request.form["file-upload"]
                g.db_cursor.execute(
                    "select title from podcasts_casts where title=%s and podcast=%s",
                    [request.form['epname'], podcastid[0]]
                )
                result = g.db_cursor.rowcount
                if ep and result is 0 and len(ep) != 0:
                    cast_upload(
                        secure_filename(ep), podcastid, request.form["epname"],
                        request.form['description'], "new"
                    )
                    return redirect(url_for('admin.show_eps', castname=castname))
                else:
                    return "Error."
            else:
                return "Not your podcast."
    else:
        abort(401)

def allowed_file(filename):
    """
    Function to check whether files are of the extensions we like.
    """
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ["mp3", "ogg", "opus", "spx"]

def cast_upload(ep_file, podcast, ep_name, ep_description, neworedit):
    """
    Function to handle podcast episode upload
    """
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
        raise
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
        g.db_cursor.execute(
            "insert into podcasts_casts (podcast, title, description, castfile, \
            date, length, filetype) values (%s,%s,%s,%s, now(),%s,%s)",
            [
                podcast[0], ep_name.strip(),
                ep_description, filepath,
                file_length, file_ext
            ]
        )
        g.db.commit()
    else:
        g.db_cursor.execute(
            "update podcasts_casts set castfile=%s, length=%s, filetype=%s where title=%s",
            [filepath, file_length, file_ext, ep_name])
        g.db.commit()

def image_upload(img, meta_array, neworedit):
    """
    Function to handle image uploads and handle DB operations for podcasts.
    """
    pil_img = Image.open(img)
    if img.filename.rsplit(".", 1)[1] in ["jpg", "jpeg", "gif", "png"]:
        if pil_img.size[0] == 1400 and pil_img.size[1] == 1400:
            filename = request.form['castname'] + "." + \
                img.filename.rsplit(".", 1)[1]
            safe_filename = secure_filename(filename)
            imgpath = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                safe_filename
            )
            # opening the request.files object (Werkzeug FileStorage) with pil
            # does "something" to it - won't save from that function. Works
            # with pil, though.
            try:
                pil_img.save(imgpath)
            except:
                return 3
            if neworedit == "edit":
                g.db_cursor.execute(
                    "update podcasts_header set name=%s, description=%s, \
                     url=%s, image=%s, categories=%s, explicit=%s where id=%s",
                    [request.form['castname'].strip(), request.form['description'],
                     request.form['url'], imgpath, request.form['category'], 
                     request.form['explicit'], meta_array[0]]
                )
                g.db.commit()
            elif neworedit == "new":
                g.db_cursor.execute(
                    "insert into podcasts_header (owner, name, description, url, \
                            image, categories, explicit) values (%s,%s,%s, %s,%s,%s,%s)",
                    [session['uid'], request.form['castname'].strip(),
                     Markup(request.form['description']).striptags(), request.form['url'],
                     imgpath, request.form['category'], request.form['explicit']]
                )
                g.db.commit()
            else:
                return "This should not happen."
            return 0
        else:
            return 1
    else:
        return 2

@admin.route("/admin/edit/<castname>/<epname>", methods=["POST", "GET"])
def edit_ep(castname, epname):
    """
    Function to edit podcast episodes.
    """
    if 'username' in session:
        podcastid = get_id("id, name, owner", castname, session['uid'])
        g.db_cursor.execute(
            "select id, podcast, title, description, castfile, filetype from podcasts_casts \
            where title=%s",
            [epname]
        )
        cast_rows = g.db_cursor.rowcount
        if cast_rows is not 0:
            cast = g.db_cursor.fetchone()
        if request.method == "GET":
            if cast_rows is not 0:
                return render_template("ep_edit.html", podcastid=podcastid, cast=cast)
            else:
                return "No such episode."
        if request.method == "POST":
            if podcastid != None:
                if request.form['epname'].strip() == "":
                    return render_template("ep_edit.html", podcastid=podcastid,
                                           error="You did not specify a valid podcast name.",
                                           cast=cast)
                if "/" in request.form['epname']:
                    return render_template("ep_edit.html", podcastid=podcastid,
                                           error="No forward slashes permitted in epsiode name.",
                                           cast=cast)
                episode_file = request.form['file-upload']
                g.db_cursor.execute(
                    "select id from podcasts_casts where title=%s",
                    [request.form['epname']]
                )
                cast_name_check = g.db_cursor.rowcount
                if cast_name_check is 0 or (cast_name_check is not 0 \
                and request.form['epname'] == cast[2]):
                    if len(episode_file) == 0:
                        secure_cast_name = secure_filename(castname)
                        secure_episode_name = secure_filename(request.form['epname'])
                        secure_file_ext = secure_filename(cast[5])

                        filepath = os.path.join(
                            current_app.config["UPLOAD_FOLDER"],
                            secure_cast_name, secure_episode_name + "." +
                            secure_file_ext
                        )
                        os.rename(cast[4], filepath)
                        g.db_cursor.execute(
                            "update podcasts_casts set castfile=%s where id=%s",
                            [filepath, cast[0]]
                        )
                        g.db.commit()
                    else:
                        try:
                            os.remove(cast[4])
                        except FileNotFoundError:
                            pass
                        cast_upload(secure_filename(episode_file), podcastid,
                                    request.form['epname'], request.form['description'], "edit")
                    g.db_cursor.execute(
                        "update podcasts_casts set title=%s, description=%s where id=%s",
                        [request.form['epname'].strip(), request.form['description'], cast[0]]
                    )
                    g.db.commit()
                    return "Success."
                else:
                    return "Already have a podcast by that name."
    else:
        abort(401)

@admin.route("/admin/delete/<castname>/<epname>")
def delete_ep(castname, epname):
    """
    Function to delete podcast episodes.
    """
    if 'username' in session:
        # 1) Does the episode exist? 2) Does it belong to the logged in user?
        podcastid = get_id("id", castname, session['uid'])
        g.db_cursor.execute(
            "select castfile from podcasts_casts where podcast=%s and title=%s",
            [podcastid[0], epname]
        )
        ep_count = g.db_cursor.rowcount
        if podcastid != None and ep_count is not 0:
            episode = g.db_cursor.fetchall()
            # Get and delete file
            for ep_found in episode:
                try:
                    os.remove(ep_found[0])
                except FileNotFoundError:
                    pass
            #Do the associated database operations
            g.db_cursor.execute(
                "delete from podcasts_casts where podcast=%s and title=%s",
                [podcastid[0], epname]
            )
            g.db.commit()
            return redirect(url_for('admin.show_casts'))
        else:
            return "Sorry, the podcast you are attempting to delete does not exist."
    else:
        abort(401)

def get_id(query, castname, owner):
    """
    Database operations helper function.
    """
    g.db_cursor.execute(
        "select " + query +" from podcasts_header where name=%s and owner=%s",
        [castname, owner]
    )
    rows = g.db_cursor.rowcount
    # emulate the behaviour of sqlite3's standard execute call
    if rows is not 0:
        return g.db_cursor.fetchone()
    else:
        return None

def validate_url(url):
    """
    URL validation helper function.
    """
    regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    is_it_a_url = match(regex, url)
    if is_it_a_url == None:
        return 1
    else:
        return 0

@admin.route("/admin/user", methods=["GET", "POST"])
def user_admin():
    """
    Function for user administration.
    """
    #FIXME: As it is, we could register with one email address then change it
    #       to an existing registration, don't think I care enough to fix.
    if 'username' in session:
        g.db_cursor.execute(
            "select username, name, email from users where id=%s",
            [session['uid']]
        )
        user_count = g.db_cursor.rowcount
        if user_count is not 0:
            user = g.db_cursor.fetchone()
        else:
            user = None
        if request.method == "GET":
            return render_template("user_admin.html", user=user)
        else:
            error = None
            if check_email(request.form['email']):
                if len(request.form['password']) == 0:
                    g.db_cursor.execute(
                        "update users set username=%s, name=%s, email=%s where id=%s",
                        [request.form['username'], request.form['name'],
                         request.form['email'], session['uid']]
                    )
                else:
                    if request.form['password'] == request.form['passwordconf']:
                        password = hash_password(request.form['password'])
                        g.db_cursor.execute(
                            "update users set username=%s, name=%s, pwhash=%s, \
                            email=%s where id=%s",
                            [request.form['username'], request.form['name'], password,
                             request.form['email'], session['uid']]
                        )
                    else:
                        return render_template("user_admin.html",
                                               error="Passwords did not match", user=user)
                g.db.commit()
            else:
                error = "Not a valid email address."
            #Call the database again to update the array that is passed to the
            #template
            g.db_cursor.execute(
                "select username, name, email from users where id=%s",
                [session['uid']]
            )
            user_count = g.db_cursor.rowcount
            if user_count is not 0:
                user = g.db_cursor.fetchone()
                return render_template("user_admin.html", user=user, error=error)
            else:
                return redirect(url_for('log.logout'))
    else:
        abort(401)

@admin.route("/admin/user/pwreset", methods=["GET", "POST"])
def pw_reset():
    """
    Function for password reset
    """
    if request.method == "GET":
        if 'username' in session:
            return redirect(url_for('admin.show_casts'))
        else:
            return render_template("password_reset.html")
    elif request.method == "POST":
       g.db_cursor.execute(
               "select * from users where username=%s and email=%s",
               [request.form['username'], request.form['email']]
        )
       valid = g.db_cursor.rowcount
       if valid > 0:
           pw_random = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(13))
           pw_hash = hash_password(pw_random)
           g.db_cursor.execute(
              "update users set pwhash=%s where username=%s and email=%s",
              [pw_hash, request.form['username'], request.form['email']]
           )
           g.db.commit()
           msg = MIMEText("Your password for user " + request.form['username']  + " has been reset to " + pw_random)
           msg["Subject"] = "Binbogami: Password reset"
           msg["From"] = "noreply@binbogami.com"
           msg["To"] = request.form['email']
           s = smtplib.SMTP('localhost')
           s.send_message(msg)
           s.quit()
           return render_template('password_reset.html', success="Password reset sucessful, check your email.")
       else:
           return render_template('password_reset.html', error="Email and password don't match those on file.")
