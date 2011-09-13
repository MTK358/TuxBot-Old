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

