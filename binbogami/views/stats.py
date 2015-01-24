from flask import Blueprint, g, current_app, abort, session, redirect, url_for
from flask import render_template
from binbogami.views.admin import get_id

stats = Blueprint("stats", __name__, template_folder="templates")

@stats.route("/stats/<castname>")
def stats_cast(castname):
  if 'username' in session:
      auth = get_id("id", castname, session['uid'])
      if auth is not None:
          xml_hits = g.sqlite_db.execute("select * from stats_xml where podcast=(?) \
              order by date desc", [auth[0]]).fetchall()
          return render_template("stats_podcast.html", podcast_name=castname, 
              xml_hits=xml_hits)
      else:
          return "Not your podcast, friend"
  else:
      return redirect(url_for('log.login'))

@stats.route("/stats/<castname>/<epname>")
def stats_ep(castname, epname):
  if 'username' in session:
    auth_podcast = get_id("id", castname, session['uid'])
    if auth_podcast is not None:
      auth_episode = g.sqlite_db.execute("select id from podcasts_casts where \
          title=(?) and podcast=(?)", [epname, auth_podcast[0]]).fetchone()
      if auth_episode is not None:
        ep_hits = g.sqlite_db.execute("select * from stats_episodes where \
            podcast=(?) and podcast_episode=(?) order by date desc",
            [auth_podcast[0], auth_episode[0]]).fetchall()
        return render_template("stats_episode.html", episode_name=epname,
            ep_hits=ep_hits)
      else:
        return "Not your episode, friend."
    else:
      return "Not your podcast, friend."
  else:
     return redirect(url_for('log.login'))

def generate_stats():
    pass
