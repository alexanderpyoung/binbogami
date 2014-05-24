from flask import Blueprint, render_template, g, request
from passlib.hash import bcrypt
from re import match

register = Blueprint("register",__name__,
                        template_folder="templates")

@register.route("/register", methods=["POST", "GET"])
def reg():
    error = None
    success = None
    if request.method == 'POST':
        userexist = g.sqlite_db.execute("select id from users where username=(?)",
                                        [request.form['username']])
        emailexist = g.sqlite_db.execute("select id from users where email=(?)",
                                        [request.form['email']])
        if len(userexist.fetchall()) != 0:
            error = "Username already in use."
        elif len(emailexist.fetchall()) != 0:
            error = "Email address already in use."
        elif not check_email(request.form["email"]):
            error = "Not a valid email address."
        else:
            passwordhashed = hash_password(request.form['password'])
            g.sqlite_db.execute(
                "insert into users (username, name, pwhash, email) values (?, ?, ?, ?)",
                [request.form['username'], request.form['name'], passwordhashed,
                request.form['email']]
            )
            g.sqlite_db.commit()
            success = "You have successfully registered!"

    return render_template("register.html", error=error, success=success)

def hash_password(password):
    pw2bytes = password.encode("utf-8")
    hashed_password = bcrypt.encrypt(pw2bytes)
    return hashed_password

def check_email(email):
    email_regex = "^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$"
    is_it_an_email = match(email_regex, email)
    if is_it_an_email == None:
        return False
    else:
        return True
