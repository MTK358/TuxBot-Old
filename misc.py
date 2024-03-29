# TuxBot, the #linux bot. Development version.
#   Copyright (C) 2011 Colson, LinuxUser324, Krenair and Tobias "ToBeFree" Frei.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/gpl-3.0.html .

import re, urllib, urllib2
from htmlentitydefs import name2codepoint

class MyHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        request = urllib2.Request(newurl)
        request.get_method = lambda: req.get_method()
        return request

urllib2.install_opener(urllib2.build_opener(MyHTTPRedirectHandler()))

def html_entity_decode(s):
    return re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)

def get_man_page(section, name):
    return "http://linux.die.net/man/%s/%s" % (section, name)

def search_man_page(name):
    return "http://duckduckgo.com/?q=site%3Alinux.die.net+" + name

def get_man_page_synopsis(section, name):
    stream = None
    try:
        stream = urllib.urlopen2(get_man_page(section, name))
        page = stream.read()
        match = re.match(r'.*<h2>Synopsis</h2>(.*)<h2>Description</h2>.*', page, flags = re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        synopsis = match.group(1)
        synopsis = re.sub(r'<br\s*/?>', "\n", synopsis)
        synopsis = re.sub(r'<[^>]*>', "", synopsis)
        synopsis = synopsis.replace("&lt;", "<")
        synopsis = synopsis.replace("&gt;", ">")
        synopsis = synopsis.replace("&amp;", "&")
        return synopsis
    except IOError:
        return None
    finally:
        if stream:
            stream.close()

def get_xkcd_url(index):
    return "https://www.xkcd.com/%d/" % (index)

def get_random_xkcd():
    return "http://dynamic.xkcd.com/random/comic/"

def translate(from_lang, to_lang, text):
    params = urllib.urlencode({"babelfishfrontpage": "yes",
                               "doit": "done",
                               "urltext": text,
                               "lp": from_lang + "_" + to_lang})
    try:
        response = urllib.urlopen2("http://babelfish.yahoo.com/translate_txt", params)
    except ioerror, e:
        return "(error: %s)" % (e)
    html = response.read().decode("iso-8859-1")
    response.close()

    match = re.search(r'<div id="result">(<div [^>]*>)?(.*?)</div>', html)
    if match:
        return html_unescape(match.group(2))


    return "(error: could not extract translated text from response)"

def get_page_title(url):
    print url
    try:
        request = urllib2.Request(url)
        request.get_method = lambda: 'HEAD'
        check = urllib2.urlopen(request)
    except:
        return "(error)"
    if 'Content-Type' not in check.headers or 'text/html' not in check.headers['Content-Type']:
        raise Exception, "Not HTML."
    if "Content-Length" in check.headers and int(check.headers["Content-Length"]) > 200000:
        raise Exception, "Content too large."

    try:
        response = urllib2.urlopen(url)
    except:
        return "(error)"
    if 'Content-Type' not in response.headers or 'text/html' not in response.headers['Content-Type']:
        raise Exception, "Not HTML."

    html = response.read() # TODO decode
    response.close()

    match = re.search(r'<title>(.+)</title>', html)
    if match:
        title = match.group(1)
        if not title:
            return "(could not extract title from page)"
        return html_entity_decode(title)

    return "(failed to read page)"

