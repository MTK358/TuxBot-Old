import urllib
import re

def get(section, name):
    return "http://linux.die.net/man/%s/%s" % (section, name)

def search(name):
    return "http://www.die.net/search/?q=%s&sa=Search&ie=ISO-8859-1&cx=partner-pub-5823754184406795%%3A54htp1rtx5u&cof=FORID%%3A9&siteurl=linux.die.net%%2F#850" % (name)

def synopsis(section, name):
    stream = None
    try:
        stream = urllib.urlopen(get(section, name))
        page = stream.read()
        print page
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


