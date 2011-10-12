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

'''
Config File Syntax:

You can configure which server, channel, nick, real name, quit message, and
command prefixes TuxBot uses. You can have multiple command prefixes
separated by double spaces:

    nick TuxBot
    realname The #Linux Bot
    channel #Linux
    server irc.esper.net 6667
    command-prefixes !  TuxBot *, *
    quitmessage Segmentation fault

Help lines define answers to questions asked using the !help command. They
consist of the word "help", followed by a space, the question in the form of
a regualr expression, two spaces, and then the answer. Here's an example:

    help example question  example answer

The answer may contain backreferences to parenthesized groups in the pattern:

    help example([0-9]+)  Number: \1

You can also set pre-defined responses when someone says something:

    on-message number ([0-9]+)  Number: \1

on-message can randomly choose from a list of responses separated by double
spaces:

    on-message example  response 1  response 2  response 3

You can run a command when a certain message matching a regular expression is
recieved using "run-command-on-message". For example, this runs the "help"
command when someone says "example":

    run-command-on-message example  help

"help", "on-message", and "run-command-on-message" all replace "\s" with the
nickname of the person TuxBot is replying to.

More of these might be added later.

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
import random

class ConfigFile:
    
    def __init__(self, path):
        self.path = path

    def get_nick(self):
        match = self._get_matching_line(re.compile('nick (.+)$'))
        if match:
            return match.group(1)
        return None

    def get_realname(self):
        match = self._get_matching_line(re.compile('realname (.+)$'))
        if match:
            return match.group(1)
        return None

    def get_quitmessage(self):
        match = self._get_matching_line(re.compile('quitmessage (.+)$'))
        if match:
            return match.group(1)
        return None

    def get_channels(self):
        match = self._get_matching_line(re.compile('channel (.+)$'))
        if match:
            return match.group(1).split(", ")
        return None

    def get_server(self):
        match = self._get_matching_line(re.compile('server (.+) (.+)$'))
        if match:
            return match.group(1), int(match.group(2))
        return None

    def get_command_prefixes(self):
        match = self._get_matching_line(re.compile('command-prefixes (.+)$'))
        if match:
            return match.group(1).split("  ")
        return None

    def get_response(self, key):
        matches = self._get_all_matching_lines(re.compile('on-message (.+?)  (.+)'))
        for match in matches:
            pattern = match.group(1)
            if re.match(pattern+"$", key):
                replacement = match.group(2).split("  ")
                replacement = replacement[random.randint(0, len(replacement) - 1)]
                return re.sub(pattern, replacement, key)
        return None

    def get_command_response(self, key):
        matches = self._get_all_matching_lines(re.compile('run-command-on-message (.+?)  (.+)'))
        for match in matches:
            pattern = match.group(1)
            if re.match(pattern+"$", key):
                replacement = match.group(2).split("  ")
                replacement = replacement[random.randint(0, len(replacement) - 1)]
                return re.sub(pattern, replacement, key)
        return None

    def get_help(self, key):
        matches = self._get_all_matching_lines(re.compile('help (.+?)  (.+)'))
        for match in matches:
            pattern = match.group(1)
            replacement = match.group(2)
            if re.match(pattern + "$", key):
                return re.sub(pattern, replacement, key)
        return None

    def get_linux_xkcds(self):
        matches = self._get_all_matching_lines(re.compile('xkcd-geek (.*)$'))
        if matches == None:
            return None;
        l = []
        for match in matches:
            l.append(match.group(1))
        return l

    def get_geek_xkcds(self):
        matches = self._get_all_matching_lines(re.compile('xkcd-geek (.*)$'))
        if matches == None:
            return None;
        l = []
        for match in matches:
            l.append(match.group(1))
        return l
    
    def _get_matching_line(self, pattern):
        f = None
        try:
            f = open(self.path, "r")
            while True:
                line = f.readline()
                if len(line) == 0:
                    break
                match = pattern.match(line)
                if match:
                    return match
        except:
            return None
        finally:
            if f:
                f.close()
        
    def _get_all_matching_lines(self, pattern):
        l = []
        f = None
        try:
            f = open(self.path, "r")
            while True:
                line = f.readline()
                if len(line) == 0:
                    break
                match = pattern.match(line)
                if match:
                    l.append(match)
            return l
        except:
            return None
        finally:
            if f:
                f.close()

