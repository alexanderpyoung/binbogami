from flask import Blueprint, render_template, g, request, redirect, url_for
from binbogami.views.log import create_session
from re import match
import passlib.hash

register = Blueprint("register",__name__,
                        template_folder="templates")

@register.route("/register", methods=["POST", "GET"])
def reg():
    error = None
    success = None
    if request.method == 'POST':
        # the standard library sqlite interface allows us to call empty returned
        # queries as None or [] for fetch()/fetchall() - psycopg2 doesn't.
        g.db_cursor.execute("select id from users where username=%s",
                                        [request.form['username']])
        userexist_rows = g.db_cursor.rowcount
        g.db_cursor.execute("select id from users where email=%s",
                                        [request.form['email']])
        emailexist_rows = g.db_cursor.rowcount 

        if userexist_rows is not 0:
            error = "Username already in use."
        elif emailexist_rows is not 0:
            error = "Email address already in use."
        elif not check_email(request.form["email"]):
            error = "Not a valid email address."
        else:
            passwordhashed = hash_password(request.form['password'])
            g.db_cursor.execute(
                "insert into users (username, name, pwhash, email) values (%s, %s, %s, %s)",
                [request.form['username'], request.form['name'], passwordhashed,
                request.form['email']]
            )
            g.db.commit()

            g.db_cursor.execute("select * from users where username=%s", [request.form["username"]])
            login_details = g.db_cursor.fetchone()
            create_session(login_details)
            return redirect(url_for('admin.show_casts'))

    return render_template("register.html", error=error)

def hash_password(password):
    pw2bytes = password.encode("utf-8")
    hashed_password = passlib.hash.bcrypt.encrypt(pw2bytes)
    return hashed_password

def check_email(email):
    email_regex = "^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$"
    is_it_an_email = match(email_regex, email)
    if is_it_an_email == None:
        return False
    else:
        return True
