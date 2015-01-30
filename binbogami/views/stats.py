from flask import Blueprint, g, current_app, abort, session, redirect, url_for
from flask import render_template
from binbogami.views.admin import get_id
from werkzeug import BaseResponse as Response
import numpy
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
from pylab import rcParams
import datetime

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

def generate_feed_stats(feed_id):
  # FIXME: there must be a less ugly way to do this
  # this doesn't provide an accurate time series, but matplotlib is fine with
  # this when datetime collections are passed
  feed_stats = g.sqlite_db.execute("select date, ip from stats_xml where podcast=(?)",
      [feed_id])
  feed_dateset = []
  feed_ip_list = []
  feed_ip_return = []
  for item in feed_stats:
    # convert the date to a "meaningful" level of granularity
    date_dt = datetime.datetime.strptime(item[0], "%Y-%m-%d %H:%M:%S.%f")
    dt_string = datetime.datetime.strftime(date_dt, "%d-%m-%y")
    date_dt_sensible = datetime.datetime.strptime(dt_string, "%d-%m-%y").date()
    # if we haven't added the date to the list, do so
    if date_dt_sensible not in feed_dateset:
      feed_dateset.append(date_dt_sensible)
      feed_ip_return.append(0)
    # we associate IP visits with dates; if no visit on a day so far, add to list
    if {'date':date_dt_sensible, 'ip':item[1]} not in feed_ip_list:
      ip_index = feed_dateset.index(date_dt_sensible)
      feed_ip_return[ip_index] = feed_ip_return[ip_index] + 1
      feed_ip_list.append({'date':date_dt_sensible, 'ip':item[1]})
  # return a tuple, because why not
  return (feed_dateset, feed_ip_return)

@stats.route("/stats/graphs/<castname>")
def graphs_cast(castname):
  if 'username' in session:
    authpodcast = get_id("id", castname, session['uid'])
    if authpodcast is not None:
      # get required data
      graph_stats = generate_feed_stats(authpodcast[0])
      # set image size
      rcParams['figure.figsize'] = 10, 5
      # plot a graph
      fig, ax = plt.subplots()
      ax.xaxis.set_major_locator(mdates.DayLocator())
      ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%y'))
      ax.set_ylim(0, max(graph_stats[1])+1)
      ax.format_xdata = mdates.DateFormatter('%d-%m-%y')
      ax.plot(graph_stats[0], graph_stats[1])
#      plt.bar(graph_stats[0], graph_stats[1], width=1.0, facecolor='green')
      fig.autofmt_xdate()
      # declare BytesIO object to stick the png in
      stringio = io.BytesIO()
      fig.savefig(stringio, format="png")
      # create a Response object with the png body and headers
      response = Response(stringio.getvalue(),mimetype="image/png") 
      return response
    else:
      return abort(403)
