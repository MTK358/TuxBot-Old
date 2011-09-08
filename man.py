import urllib
import re

def get(section, name):
    return "http://linux.die.net/man/%s/%s" % (section, name)

def search(name):
    return "http://duckduckgo.com/?q=site%3Alinux.die.net+" + name

def synopsis(section, name):
    stream = None
    try:
        stream = urllib.urlopen(get(section, name))
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

