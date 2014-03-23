#TODO: Remove distinction between incorrect username and password

from flask import g, session, render_template, Blueprint, request, redirect
from flask import url_for
from passlib.hash import bcrypt

log = Blueprint("log", __name__, template_folder="templates")

@log.route("/login", methods=["POST", "GET"])
def login():
    error = None
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        user = g.sqlite_db.execute("select * from users where username=(?)",
                                    [request.form["username"]])
        row = user.fetchone()
        if row == None:
            error = "No such user."
            return render_template("login.html", error=error)
        else:
            if bcrypt.verify(request.form["password"], row[3]):
                session['uid'] = row[0]
                session['username'] = row[1]
                session['name'] = row[2]
                return redirect(url_for('admin.show_casts'))
            else:
                error = "Bad password."
                return render_template("login.html", error=error)

@log.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('frontpage.index'))
    