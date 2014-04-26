from flask import Blueprint, render_template, g, request
from passlib.hash import bcrypt

register = Blueprint("register",__name__,
                        template_folder="templates")
                        
@register.route("/register", methods=["POST", "GET"])
def reg():
    error = None
    success = None
    if request.method == 'POST':
        userexist = g.sqlite_db.execute("select id from users where username=(?)",
                                        [request.form['username']])
        if len(userexist.fetchall()) != 0:
            error = "Username already in use."
        else:
            passwordhashed = hash_password(request.form['password'])
            g.sqlite_db.execute(
                "insert into users (username, name, pwhash) values (?, ?, ?)",
                [request.form['username'], request.form['name'], passwordhashed]
            )
            g.sqlite_db.commit()
            success = "You have successfully registered!"
            
    return render_template("register.html", error=error, success=success)

def hash_password(password):
    pw2bytes = password.encode("utf-8")
    hashed_password = bcrypt.encrypt(pw2bytes)
    return hashed_password
