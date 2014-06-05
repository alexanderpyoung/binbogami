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
            error = "Incorrect username and password, please try again."
            return render_template("login.html", error=error)
        else:
            if bcrypt.verify(request.form["password"], row[3]):
                create_session(row)
                return redirect(url_for('admin.show_casts'))
            else:
                error = "Incorrect username and password, please try again."
                return render_template("login.html", error=error)

@log.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('frontpage.index'))

def create_session(session_information):
    session['uid'] = str(session_information[0])
    session['username'] = session_information[1]
    session['name'] = session_information[2]
