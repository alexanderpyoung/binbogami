"""Module to handle serving XML, images, media"""
from flask import Blueprint, g, send_from_directory, current_app
from flask import Markup, request, Response, abort, session
from werkzeug.utils import secure_filename
import lxml.etree as ET
from datetime import datetime
from urllib.parse import quote
import os, mimetypes, re

serve = Blueprint("serve", __name__, template_folder="templates")

@serve.route("/<castname>/<epname>")
def serve_file(castname, epname):
    """
    Serves podcast media, takes castname and epname as arguments.
    """
    safe_podcast_name = secure_filename(castname)
    safe_episode_name = secure_filename(epname).rsplit(".")[0]
    safe_name = safe_podcast_name + "/" + safe_episode_name
    safe_ext = secure_filename(epname).rsplit(".")[-1]
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], safe_name + "." + safe_ext)
    if os.path.isfile(filepath):
        if 'name' not in session:
            epname_noext = epname.rsplit(".")[0]
            stats_update_episode(epname_noext)
        return send_file_206(filepath, safe_name, safe_ext)
    else:
        abort(404)

@serve.after_request
def after_request(response):
    """
    Adds range header to all served requests.
    """
    response.headers.add('Accept-Ranges', 'bytes')
    return response


def send_file_206(path, safe_name, safe_ext):
    """
    Handling for partial downloads of media files (Safari's streaming, iOS)
    """
    range_header = request.headers.get('Range', None)
    if not range_header:
        return send_from_directory(current_app.config["UPLOAD_FOLDER"], safe_name + '.' + safe_ext)

    size = os.path.getsize(path)
    byte1, byte2 = 0, None

    match = re.search('(\d+)-(\d*)', range_header)
    group = match.groups()

    if group[0]:
        byte1 = int(group[0])
    if group[1]:
        byte2 = int(group[1])

    length = size - byte1
    if byte2 is not None:
        length = byte2 - byte1 + 1

    data = None
    with open(path, 'rb') as media_file:
        media_file.seek(byte1)
        data = media_file.read(length)

    response_value = Response(data,
                              206,
                              mimetype=mimetypes.guess_type(path)[0],
                              direct_passthrough=True)
    response_value.headers.add('Content-Range',
                               'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, size))
    return response_value

@serve.route("/image/<img_name>")
def serve_image(img_name):
    """
    Function to serve images
    """
    img_send = img_name.replace(" ", "_")
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                               secure_filename(img_send))

@serve.route("/<castname>/feed")
def serve_xml(castname):
    """
    A function to fetch podcast episode data, before passing it to build_xml()
    """
    g.db_cursor.execute(
        "select * from podcasts_header where name=%s",
        [castname]
    )
    cast_rows = g.db_cursor.rowcount
    if cast_rows is not 0:
        cast_meta = g.db_cursor.fetchone()
        g.db_cursor.execute(
            "select * from podcasts_casts where podcast=%s order by date desc",
            [cast_meta[0]]
        )
        if g.db_cursor.rowcount is not 0:
            episodes = g.db_cursor.fetchall()
        else:
            episodes = []
        g.db_cursor.execute(
            "select name from users where id=%s",
            [cast_meta[1]]
        )
        name = g.db_cursor.fetchone()
        stats_update_xml(cast_meta[0])
        return build_xml(cast_meta, episodes, name)
    else:
        return "No such cast."

def build_xml(meta, casts, name):
    """
    A function to generate podcast XML
    """
    #General XML structure
    encoded_feed_url = request.url_root + quote(meta[2]) + "/feed"
    cast_img_list = meta[5].rsplit("/")
    cast_img = cast_img_list[len(cast_img_list)-1]
    #TODO: Editorship, TTL; SkipDays/Hours
    rss = ET.Element('rss',
                     {
                         'version':'2.0',
                     },
                     {
                         "atom" : "http://www.w3.org/2005/Atom",
                         "itunes" : "http://www.itunes.com/dtds/podcast-1.0.dtd"
                     }
                    )
    channel = ET.SubElement(rss, 'channel')
    podcast_title = ET.SubElement(channel, 'title')
    podcast_description = ET.SubElement(channel, 'description')
    podcast_link = ET.SubElement(channel, 'link')
    ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link',
                  {
                      'rel' : 'self',
                      'href' : encoded_feed_url
                  }
                 )
    podcast_image = ET.SubElement(channel, 'image')
    podcast_image_url = ET.SubElement(podcast_image, 'url')
    podcast_image_link = ET.SubElement(podcast_image, 'link')
    podcast_image_width = ET.SubElement(podcast_image, 'width')
    podcast_image_height = ET.SubElement(podcast_image, 'height')
    podcast_image_title = ET.SubElement(podcast_image, 'title')
    podcast_copyright = ET.SubElement(channel, 'copyright')
    podcast_generator = ET.SubElement(channel, 'generator')

    #Populate elements with relevant data
    podcast_title.text = meta[2]
    podcast_description.text = meta[3]
    podcast_link.text = meta[4]
    podcast_image_url.text = request.url_root + "image/" + cast_img
    podcast_image_link.text = meta[4]
    podcast_image_width.text = '144'
    podcast_image_height.text = '144'
    podcast_image_title.text = meta[2]
    podcast_copyright.text = "Licensed under the Open Audio License."
    podcast_generator.text = "Binbogami"

    #iTunes tags
    podcast_itunes_explicit = ET.SubElement(channel,
                                            '{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit')
    podcast_itunes_author = ET.SubElement(channel,
                                          '{http://www.itunes.com/dtds/podcast-1.0.dtd}author')
    podcast_itunes_subtitle = ET.SubElement(channel,
                                            '{http://www.itunes.com/dtds/podcast-1.0.dtd}subtitle')
    podcast_itunes_category = ET.SubElement(channel,
                                            '{http://www.itunes.com/dtds/podcast-1.0.dtd}category')
    podcast_itunes_image = ET.SubElement(channel,
                                         '{http://www.itunes.com/dtds/podcast-1.0.dtd}image')

    #iTunes population
    podcast_itunes_author.text = name[0]
    podcast_itunes_subtitle.text = meta[3]
    podcast_itunes_category.text = meta[6]
    podcast_itunes_image.text = request.url_root + "image/" + cast_img
    podcast_itunes_explicit.text = meta[7]

    #now for the items for each podcast.
    for cast in casts:
        #Some variable-setting
        cast_length = cast[6]
        encoded_url = request.url_root + quote(meta[2]) + "/" + \
                      quote(cast[2]) + "." + quote(cast[7])
        if cast[7] == "mp3":
            mime_type = "audio/mpeg"
        else:
            mime_type = "audio/ogg"
        #Structure
        cast_item = ET.SubElement(channel, 'item')
        cast_title = ET.SubElement(cast_item, 'title')
        cast_description = ET.SubElement(cast_item, 'description')
        cast_date = ET.SubElement(cast_item, 'pubDate')
        ET.SubElement(cast_item, 'enclosure',
                      {
                          'length': str(round(float(cast_length))),
                          'url': encoded_url,
                          'type': mime_type
                      }
                     )
        cast_guid = ET.SubElement(cast_item, 'guid',
                                  {
                                      'isPermaLink':"true"
                                  }
                                 )

        #Content
        cast_title.text = cast[2]
        cast_description.text = cast[3]
        cast_date.text = datetime.strftime(cast[5], "%a, %d %b %Y %H:%M:%S %z")
        cast_guid.text = encoded_url

    #XML miscellanea
    doctype = '<?xml version="1.0" encoding="utf-8" ?>\n'
    body = ET.tostring(rss, encoding="UTF-8", method="xml", pretty_print="True").decode("utf-8")
    return Markup(doctype + body)

def stats_update_xml(cast):
    """
    A function to update the stats each time the XML is served.
    """
    #we pass the integer id in here as we've already done the query for XML serving
    referrer = request.referrer
    access_ip = request.remote_addr
    date = str(datetime.now())
    g.db_cursor.execute("insert into stats_xml (podcast, date, ip, referrer) values \
                        (%s, %s, %s, %s)", [cast, date, access_ip, referrer])
    g.db.commit()

def stats_update_episode(episode):
    """
    A function to update stats when a file is served, IF the user is not logged in.
    """
    referrer = request.referrer
    access_ip = request.remote_addr
    date = str(datetime.now())
    # otherwise we get multiple entries from 206es
    # this is based on Firefox's behaviour - Safari probably does something awful
    if referrer is None or episode not in referrer:
        g.db_cursor.execute("select id, podcast from podcasts_casts where title = %s",
                            [episode])
        db_cursor_ids = g.db_cursor.fetchone()
        episode_id = db_cursor_ids[0]
        podcast_id = db_cursor_ids[1]
        g.db_cursor.execute("insert into stats_episodes (podcast, \
                            podcast_episode, date, ip, referrer) values \
                            (%s, %s, %s, %s, %s)", [podcast_id, episode_id,
                                                    date, access_ip, referrer])
        g.db.commit()

