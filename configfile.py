'''
Config File Syntax:

Help lines define answers to questions asked using the !help command. They
consist of the word "help", followed by a space, the question, two spaces,
and then the answer. Here's an example:

    help example question  example answer

If you use "help-re" instead of "help", the question is a regular expression
and the answer can contain backreferences. For example:

    help-re example([0-9]+)  Number: \1

You can also add comics to the list that !xkcd-linux and !xkcd-geek pick
randomly from:

    xkcd-linux 123
    xkcd-linux 321
    xkcd-geek 456
    xkcd-geek 654

Even though the parser ignores invalid lines for now, it might be a good idea
to prepend comments with a "#" character, both to be safe and to be ready for
possible future changes:

    # this line is ignored by the config file parser
'''
import re

class ConfigFile:
    
    def __init__(self, path):
        self.path = path

    def get_help(self, key):
        escaped_key = re.escape(key)
        f = None
        try:
            f = open(self.path, "r")
            while True:
                line = f.readline()
                if len(line) == 0:
                    break
                match = re.match("help "+escaped_key+"  (.+)$", line)
                if match:
                    return match.group(1)
                match = re.match("help-re (.+?)  (.+)$", line)
                if match:
                    pattern = match.group(1)
                    replacement = match.group(2)
                    if re.match(pattern+"$", key):
                        return re.sub(pattern, replacement, key)
        except:
            return None
        finally:
            if f:
                f.close()

    def get_linux_xkcds(self):
        l = []
        f = None
        try:
            f = open(self.path, "r")
            while True:
                line = f.readline()
                if len(line) == 0:
                    break
                match = re.match("xkcd-linux (.+)$", line)
                if match:
                    l.append(match.group(1))
            return l
        except:
            return None
        finally:
            if f:
                f.close()

    def get_geek_xkcds(self):
        l = []
        f = None
        try:
            f = open(self.path, "r")
            while True:
                line = f.readline()
                if len(line) == 0:
                    break
                match = re.match("xkcd-geek (.+)$", line)
                if match:
                    l.append(match.group(1))
            return l
        except:
            return None
        finally:
            if f:
                f.close()

