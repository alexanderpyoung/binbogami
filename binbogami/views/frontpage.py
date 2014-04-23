from flask import Blueprint, session, render_template

frontpage = Blueprint("frontpage",__name__,
                      template_folder="templates")

@frontpage.route("/")
def index():
    if 'name' in session: 
        return render_template("frontpage.html", user=session['name'])
    else:
        return render_template("frontpage.html")