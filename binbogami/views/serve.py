from flask import Blueprint, g, session, send_from_directory, current_app
from flask import Markup, request
from werkzeug.utils import secure_filename
from binbogami.views.admin import get_id
from lxml import etree as ET
from datetime import datetime
from urllib.parse import quote

serve = Blueprint("serve", __name__, template_folder="templates")

@serve.route("/<castname>/<epname>")
def serve_file(castname, epname):
    safe_filename = secure_filename(castname + " - " + epname)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                                safe_filename.replace(" ", "_"))

@serve.route("/image/<img_name>")
def serve_image(img_name):
    img_send = img_name.replace(" ", "_")
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                                secure_filename(img_send))

@serve.route("/<castname>/feed")
def serve_xml(castname):
    cast_meta = g.sqlite_db.execute(
        "select * from podcasts_header where name=(?)",
        [castname]
    ).fetchone()
    if cast_meta != None:
        episodes = g.sqlite_db.execute(
            "select * from podcasts_casts where podcast=(?) order by date desc",
            [cast_meta[0]]
        ).fetchall()
        name = g.sqlite_db.execute(
            "select name from users where id=(?)",
            [cast_meta[1]]
        ).fetchone()
        return build_xml(cast_meta, episodes, name)
    else:
        return "No such cast."

def build_xml(meta, casts, name):
    #General XML structure
    encoded_feed_url = request.url_root + quote(meta[2]) + "/feed"
    cast_img_list = meta[5].rsplit("/")
    cast_img = cast_img_list[len(cast_img_list)-1]
    #TODO: Categories; Editorship, TTL; SkipDays/Hours; iTunes?
    rss = ET.Element('rss',
                        {
                            'version':'2.0',
                         },
                         nsmap = {
                             "atom" : "http://www.w3.org/2005/Atom",
                             "itunes" : "http://www.itunes.com/dtds/podcast-1.0.dtd"
                         }
                    )
    channel = ET.SubElement(rss, 'channel')
    podcast_title = ET.SubElement(channel, 'title')
    podcast_description = ET.SubElement(channel, 'description')
    podcast_link = ET.SubElement(channel, 'link')
    podcast_atom_link = ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link',
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
    podcast_itunes_author = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}author')
    podcast_itunes_subtitle = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}subtitle')
    podcast_itunes_category = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}category')
    podcast_itunes_image = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}image')

    #iTunes population
    podcast_itunes_author.text = name[0]
    podcast_itunes_subtitle.text = meta[3]
    podcast_itunes_category.text = meta[6]
    podcast_itunes_image.text = request.url_root + "image/" + cast_img

    #now for the items for each podcast. Thankfully fucking iterable.
    for cast in casts:
        #Some variable-setting
        encoded_url = request.url_root + quote(meta[2]) + "/" + quote(cast[2]) + "." + quote(cast[7])
        if cast[7] == "mp3":
            mime_type = "audio/mpeg"
        else:
            mime_type = "audio/ogg"
        #Structure
        cast_item = ET.SubElement(channel, 'item')
        cast_title = ET.SubElement(cast_item, 'title')
        cast_description = ET.SubElement(cast_item, 'description')
        cast_date = ET.SubElement(cast_item, 'pubDate')
        cast_enclosure = ET.SubElement(cast_item, 'enclosure',
                            {
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
        cast_date.text = datetime.strptime(cast[5], "%Y-%m-%d %H:%M:%S").strftime("%a, %d %b %Y %H:%M:%S %z") + "+0000"
        cast_guid.text = encoded_url

    #XML miscellanea
    doctype = '<?xml version="1.0" encoding="utf-8" ?>\n'
    body = ET.tostring(rss, encoding="UTF-8", method="xml", pretty_print="True").decode("utf-8")
    stats_update_xml(meta[0])
    return Markup(doctype + body)

def stats_update_xml(cast):
    g.sqlite_db.execute("insert into stats_xml (podcast, date) values (?, datetime('now'))",
                        [cast])
    g.sqlite_db.commit()

def stats_update_episode(episode):
    pass
