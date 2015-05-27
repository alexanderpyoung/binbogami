from flask import Blueprint, g, current_app, abort, session, redirect, url_for
from flask import render_template
from binbogami.views.admin import get_id
from werkzeug import BaseResponse as Response
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import io
from pylab import rcParams
import datetime


stats = Blueprint("stats", __name__, template_folder="templates")


@stats.route("/stats/<castname>")
def stats_cast(castname):
    if 'username' in session:
        auth = get_id("id", castname, session['uid'])
        if auth is not None:
            g.db_cursor.execute("select * from stats_xml where podcast=%s \
                                order by date desc", [auth[0]])
            xml_rows = g.db_cursor.rowcount
            if xml_rows is not 0:
                xml_hits = g.db_cursor.fetchall()
            else:
                xml_hits = []
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
            g.db_cursor.execute("select id from podcasts_casts where \
                                title=%s and podcast=%s", [epname, auth_podcast[0]])
            auth_count = g.db_cursor.rowcount
            if auth_count is not 0:
              auth_episode = g.db_cursor.fetchone()
              g.db_cursor.execute("select * from stats_episodes where \
                                  podcast=%s and podcast_episode=%s order by \
                                  date desc",
                                  [auth_podcast[0], auth_episode[0]])
              ep_hits = g.db_cursor.fetchall()
              return render_template("stats_episode.html", episode_name=epname,
                                     ep_hits=ep_hits, podcast_name=castname)
            else:
              return "Not your episode, friend."
          else:
            return "Not your podcast, friend."
    else:
        return redirect(url_for('log.login'))

def generate_date(orig):
      # convert the date to a "meaningful" level of granularity
      dt_string = datetime.datetime.strftime(orig, "%d-%m-%y")
      date_dt_sensible = datetime.datetime.strptime(dt_string, "%d-%m-%y").date()
      return date_dt_sensible

def generate_feed_stats(feed_id, starttime, endtime, ep_id=None):
    # FIXME: there must be a less ugly way to do this
    # this doesn't provide an accurate time series, but matplotlib is fine with
    # this when datetime collections are passed
    if ep_id is None:
      g.db_cursor.execute("select date, ip from stats_xml where \
                          podcast=%s and date between %s and %s", \
                          [feed_id, starttime, endtime])
      if g.db_cursor.rowcount is not 0:
          feed_stats = g.db_cursor.fetchall()
      else:
          feed_stats = []
    else:
        g.db_cursor.execute("select date, ip from stats_episodes \
                            where podcast=%s and podcast_episode=%s \
                            and date between %s and %s",
                            [feed_id, ep_id, starttime, endtime])
    if g.db_cursor.rowcount is not 0:
        feed_stats = g.db_cursor.fetchall()
    else:
        feed_stats = []
    feed_dateset = []
    feed_ip_list = []
    feed_ip_return = []
    for item in feed_stats:
        date_dt_sensible = generate_date(item[0])
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

def shared_graphing(list_date, list_ip):
    # set image size
    rcParams['figure.figsize'] = 10, 5
    # plot a graph, if our list isn't empty
    if list_ip:
        fig, ax = plt.subplots()
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%y'))
        ax.yaxis.set_major_locator(ticker.MultipleLocator())
        ax.set_ylim(0, max(list_ip)+1)
        ax.format_xdata = mdates.DateFormatter('%d-%m-%y')
        ax.bar(list_date, list_ip, width=1.0, facecolor='green', align='center')
        ax.plot(list_date, list_ip, 'yo-')
        fig.autofmt_xdate()
    # otherwise, show an image of nothing
    else:
        fig = plt.figure()
        plt.figtext(0.42, 0.5, "No data for this query.")
    # declare BytesIO object to stick the png in
    stringio = io.BytesIO()
    fig.savefig(stringio, format="png")
    return stringio.getvalue()

# when we use SQLite 'between', it's an exclusive limit. Add a day.
@stats.route("/stats/graphs/<castname>", \
             defaults={'starttime': (datetime.datetime.now().date() + 
             datetime.timedelta(days=1)) - datetime.timedelta(days=7),
             'endtime': datetime.datetime.now().date() + 
             datetime.timedelta(days=1)})
@stats.route("/stats/graphs/<castname>/<starttime>/<endtime>")
def graphs_cast(castname, starttime, endtime):
    if 'username' in session:
        authpodcast = get_id("id", castname, session['uid'])
        if authpodcast is not None:
            # get required data
            graph_stats = generate_feed_stats(authpodcast[0], starttime, endtime)
            # build graph
            graph_img = shared_graphing(graph_stats[0], graph_stats[1])
            # create a Response object with the png body and headers
            response = Response(graph_img,mimetype="image/png") 
            return response
        else:
            return abort(403)
    else:
        return abort(403)

@stats.route("/stats/graphs/<castname>/<epname>",
    defaults={'starttime': (datetime.datetime.now().date() +
              datetime.timedelta(days=1)) - datetime.timedelta(days=7),
              'endtime': datetime.datetime.now().date() +
              datetime.timedelta(days=1)})
@stats.route("/stats/graphs/<castname>/<epname>/<starttime>/<endtime>")   
def graphs_ep(castname,epname, starttime, endtime):
    if 'username' in session:
        authpodcast = get_id("id", castname, session['uid'])
        if authpodcast is not None:
            g.db_cursor.execute("select id from podcasts_casts where \
                                podcast=%s and title=%s", [authpodcast[0],
                                epname])
            authepisode_rows = g.db_cursor.rowcount
            if authepisode_rows is not 0:
                authepisode = g.db_cursor.fetchone()
                graph_stats = generate_feed_stats(authpodcast[0], starttime, endtime,
                                                  authepisode[0])
                graph_img = shared_graphing(graph_stats[0], graph_stats[1])
                response = Response(graph_img, mimetype="image/png")
                return response
            else:
                return abort(403)
        else:
            return abort(403)
    else:
        return abort(403)
