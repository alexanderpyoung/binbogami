from binbogami import bbgapp

@bbgapp.route("/")
def index():
    return "Hello world!"
