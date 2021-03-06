"""
Module to handle logging in and logging out.
"""
from flask import g, session, render_template, Blueprint, request, redirect
from flask import url_for
import passlib.hash

log = Blueprint("log", __name__, template_folder="templates")

@log.route("/login", methods=["POST", "GET"])
def login():
    """
    Display login page and handle submissions.
    """
    error = None
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        g.db_cursor.execute("select * from users where username=%s",
                            [request.form["username"]])
        row = g.db_cursor.rowcount
        if row is 0:
            error = "Incorrect username and password, please try again."
            return render_template("login.html", error=error)
        else:
            fetch = g.db_cursor.fetchone()
            if passlib.hash.bcrypt.verify(request.form["password"], fetch[3]):
                create_session(fetch)
                return redirect(url_for('admin.show_casts'))
            else:
                error = "Incorrect username and password, please try again."
                return render_template("login.html", error=error)

@log.route("/logout")
def logout():
    """
    Destroy session cookies.
    """
    session.clear()
    return redirect(url_for('frontpage.index'))

def create_session(session_information):
    """
    Create session.
    """
    session['uid'] = str(session_information[0])
    session['username'] = session_information[1]
    session['name'] = session_information[2]
