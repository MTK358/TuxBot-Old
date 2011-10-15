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


from irc import IrcClient
from configfile import ConfigFile
import xkcd
import man
import re
import sys
import time
import random
import os
import getpass
import signal
import datetime
import select
import Time

if len(sys.argv) != 2:
    print "Usage: " + sys.argv[0] + " path/to/config/file"
    sys.exit(1)
config = ConfigFile(sys.argv[1])

server, port = config.get_server()
if not server:
    print "Config file has no server entry"
    sys.exit(1)
channels = config.get_channels()
if not channels:
    print "Config file has no channel entry"
    sys.exit(1)
nick = config.get_nick()
if not nick:
    print "Config file has no nick entry"
    sys.exit(1)
realname = config.get_realname()
if not realname:
    print "Config file has no realname entry"
    sys.exit(1)
quitmessage = config.get_quitmessage()
if not quitmessage:
    print "Config file has no quitmessage entry"
    sys.exit(1)
command_prefixes = config.get_command_prefixes()
if not command_prefixes:
    print "Config file has no command-prefixes entry"
    sys.exit(1)

pipe = os.popen('git log --pretty=format:"git commit %h (%s)"')
version = pipe.readline().strip()
pipe.close()

commandref = '''!help <key> -- get help about <key>
!man <section> <name> -- get the URL to an online man page
!synopsis <section> <name> -- get the SYNOPSIS section of the specified man page
!man <criteria> -- search for an online man page
!xkcd -- get a link to a random xkcd comic
!xkcd <number> -- get the link to the specified xkcd
!xkcd-linux -- get a random xkcd comic that mentions Linux
(Note: you can use "geek" instead of "linux" in the above command for geeky comics)
!time -- show the current time
!time <strftime> -- show the current time, with custom formatting. See "man strftime" for more.
(Note: you can use "date" instead of "time" in the above two commands)
!license or !credits or !authors -- view the license information and the names of the people who made TuxBot.'''

opcommandref = '''!quit -- make TuxBot quit'''

license = '''Copyright (C) 2011 Colson, LinuxUser324, Krenair and Tobias "ToBeFree" Frei.
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
---
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
---
http://www.gnu.org/licenses/gpl-3.0.html'''

def clean_string(string):
    return re.sub("\s+", " ", re.sub("[^-_\w\s]", "", string.lower()))

def process_command(line, sender, channel):
    # !help -- get help about TuxBot's commads
    match = re.match(r'help$', line)
    if match:
        irc.send_private_notice(commandref, sender)
        if sender in channel_ops[channel] + channel_voices[channel]:
            irc.send_private_notice(opcommandref, sender)
        return True

    # !help <key> -- get help
    match = re.match(r'help\s+(.*)$', line)
    if match:
        key = clean_string(match.group(1))
        text = config.get_help(key)
        if text:
            irc.send_message("%s" % (text), channel)
        else:
            irc.send_message("I don't have an answer for \"%s\". You can set it using the \"!sethelp question: answer\" command." % (key), channel)
        return True

    # !man <section> <name> -- get the URL to an online man page
    match = re.match(r'man\s+(\w+)\s+([-A-Za-z0-9_]+)$', line)
    if match:
        irc.send_message(man.get(match.group(1), match.group(2)), channel)
        return True
    # !synopsis <section> <name> -- print the "SYNOPSIS" section of the specified man page
    match = re.match(r'synopsis\s+(\w+)\s+(\w+)$', line)
    if match:
        text = man.synopsis(match.group(1), match.group(2))
        if not text:
            irc.send_message("Failed to get man page for \"%s\" in section \"%s\"" % (match.group(2), match.group(1)), channel)
            return True
        irc.send_message(text, channel)
        return True
    # !man <criteria> -- search for an online man page
    match = re.match(r'man\s+(\w+)$', line)
    if match:
        irc.send_message(man.search(match.group(1)), channel)
        return True

    # !xkcd -- get a random xkcd comic
    match = re.match(r'xkcd$', line)
    if match:
        irc.send_message(xkcd.get_random(), channel)
        return True
    # !xkcd <index> -- get an xkcd comic by index
    match = re.match(r'xkcd\s+([0-9]+)$', line)
    if match:
        irc.send_message(xkcd.get_url(int(match.group(1))), channel)
        return True

    # !xkcd-linux and !xkcd-geek -- get linux-related and geeky xkcd comics
    match = re.match(r'xkcd-linux$', line)
    if match:
        l = config.get_linux_xkcds()
        if not l:
            irc.send_message("No linux-related comics in list.", channel)
        else:
            irc.send_message(xkcd.get_url(int(l[random.randint(0, len(l)-1)])), channel)
        return True
    match = re.match(r'xkcd-geek$', line)
    if match:
        l = config.get_geek_xkcds()
        if not l:
            irc.send_message("No linux-related comics in list.", channel)
        else:
            irc.send_message(xkcd.get_url(int(l[random.randint(0, len(l)-1)])), channel)
        return True

    # !wikipedia -- get a random wikipedia article
    match = re.match(r'wikipedia$', line)
    if match:
        irc.send_message("http://en.wikipedia.org/wiki/Special:Random", channel)
        return True
    # !wikipedia <article> -- get a link to wikipedia article
    match = re.match(r'wikipedia\s+([^\s].+)$', line)
    if match:
        irc.send_message("http://en.wikipedia.org/wiki/Special:Search?search=" + clean_string(match.group(1)).replace(" ", "+"), channel)
        return True
    # !wikipedia-<lang> -- get a random wikipedia article in a certain language
    match = re.match(r'wikipedia-(\w+)$', line)
    if match:
        irc.send_message("http://"+match.group(1)+".wikipedia.org/wiki/Special:Random", channel)
        return True
    # !wikipedia-<lang> <article> -- get a link to wikipedia article in a certain language
    match = re.match(r'wikipedia-(\w+)\s+([^\s].+)$', line)
    if match:
        irc.send_message("http://"+match.group(1)+".wikipedia.org/wiki/Special:Search?search=" + clean_string(match.group(2)).replace(" ", "+"), channel)
        return True

    # !time and !date -- get the current time
    match = re.match(r'(time|date)$', line)
    if match:
        irc.send_message(time.strftime("%A %Y-%m-%d %H:%M:%S %Z"), channel)
        return True
    match = re.match(r'(time|date)\s+([^\s].*)$', line)
    if match:
        irc.send_message(time.strftime(match.group(2)), channel)
        return True

    # !license or !authors or !credits -- display license information and the names of the people who made TuxBot
    match = re.match(r'credits|authors|license$', line)
    if match:
        irc.send_private_notice(license, sender)
        return True

    #!user -- display the username which this python script is running under
    match = re.match(r'user$', line)
    if match:
        irc.send_message(getpass.getuser(), channel)
        return True

    # !version -- get TuxBot's version. Assumes that TuxBot is run from its git repository directory
    match = re.match(r'version$', line)
    if match:
        irc.send_message(version, channel)
        return True

    # !quit -- make TuxBot quit
    match = re.match(r'quit$', line)
    if match:
        if sender not in channel_ops[channel] + channel_voices[channel]:
            irc.send_message(sender + ": Permission denied. You must be +o or +v.", channel)
        else:
            irc.quit(quitmessage)
            sys.exit(0)
        return True

    return False

def process_message(line, to, sender):
    line = line.strip()
    if to == nick:
        #private message
        if line == "VERSION":
            irc.send_private_notice("VERSION " + version + "", sender)
        elif line == "TIME":
            irc.send_private_notice("TIME " + datetime.datetime.now().strftime("%a %b %d %H:%M:%S") + "", sender)
        #elif line
        #FINGER        - Returns the user's full name, and idle time.
        #SOURCE        - Where to obtain a copy of a client.
        #USERINFO    - A string set by the user (never the client coder)
        #CLIENTINFO    - Dynamic master index of what a client knows.
        #ERRMSG        - Used when an error needs to be replied with.
        #PING        - Used to measure the delay of the IRC network between clients.
        return
    for command_prefix in command_prefixes:
        if re.match(command_prefix, line) and process_command(line[len(command_prefix):], sender, to):
            return
    response = config.get_response(clean_string(line))
    if response:
        irc.send_message(response.replace("\\s", sender), to)
        return

flood_data = {} # channel as keywords, with the value as an array containing [user, timestamp, count]

def flood_check(target, sender):
    if target != nick and target in flood_data.keys():
        if sender == flood_data[target][0] and Time.time() < flood_data[target][1] + 0.5:
            flood_data[target][2] += 1
        if flood_data[target][2] >= 5:
            # send kick message
            del flood_data[target]
    else:
        flood_data[target] = [user,Time.time(),1]

channel_ops = {}
channel_voices = {}

def process_mode(modeset):
    try:
        if modeset.to[0] == "#":
            channel = modeset.to
        else:
            return

        if channel_ops[channel] == None:
            channel_ops[channel] = []
        elif channel_voices[channel] == None:
            channel_voices[channel] = []

        if modeset.mode is "o" and modeset.given:
            channel_ops[channel].append(modeset.nick)
        elif modeset.mode is "o" and not modeset.given:
            channel_ops[channel].remove(modeset.nick)
        elif modeset.mode is "v" and modeset.given:
            channel_voices[channel].append(modeset.nick)
        elif modeset.mode is "v" and not modeset.given:
            channel_voices[channel].remove(modeset.nick)
    except KeyError:
        pass
    except ValueError:
        pass
    #modeset: setter, to, mode, given[, nick]

def process_kick(kicker, channel, nick, comment):
    try:
        channel_ops[channel].remove(nick)
    except ValueError:
        pass

    try:
        channel_voices[channel].remove(nick)
    except ValueError:
        pass

def process_quit(nick, comment):
    for channel in channel_ops:
        try:
            channel.remove(nick)
        except ValueError:
            pass

    for channel in channel_voices:
        try:
            channel.remove(nick)
        except ValueError:
            pass

def process_part(nick, channel):
    try:
        channel_ops[channel].remove(nick)
    except ValueError:
        pass

    try:
        channel_voices[channel].remove(nick)
    except ValueError:
        pass

def process_name(name, channel):
    if channel not in channel_ops:
        channel_ops[channel] = []
    
    if channel not in channel_voices:
        channel_voices[channel] = []

    if name[:1] == '@':
        channel_ops[channel].append(name[1:])
    elif name[:1] == "+":
        channel_voices[channel].append(name[1:])

irc = IrcClient(server, port, nick, realname)
joined = False

def signal_handler(signal, frame):
    irc.quit(quitmessage)
    print ''
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

while True:
    s = select.select([irc.socket, sys.stdin], [], [])[0]
    if sys.stdin in s:
        irc.socket.send(sys.stdin.readline().strip() + "\r\n")

    if irc.socket in s:
        line = irc.readline()
        if line is "" or line is None:
            continue
        print line

        # respond to PING commands
        tmp = irc.is_ping(line)
        if tmp:
            irc.send_pong(tmp)
            continue

        if not joined and line == ":"+nick+" MODE "+nick+" :+i":
            for channel in channels:
                irc.join(channel)
            joined = True

        if not joined:
            continue

        # respond to posts on the channel
        tmp = irc.is_message(line)
        if tmp is not None:
            process_message(tmp[2], tmp[1], tmp[0])
            flood_check(tmp[1],tmp[0]):
            continue

        tmp = irc.is_quit(line)
        if tmp is not None:
            process_quit(tmp[0], tmp[1])
            continue

        tmp = irc.is_kick(line)
        if tmp is not None:
            process_kick(tmp[0], tmp[1], tmp[2], tmp[3])
            continue

        tmp = irc.is_part(line)
        if tmp is not None:
            for channel in tmp[1]:
                process_part(tmp[0], channel)
            continue

        tmp = irc.is_mode(line)
        if tmp is not None:
            for i in tmp:
                process_mode(i)
            continue

        tmp = irc.is_names(line)
        if tmp is not None:
            for name in tmp[1:]:
                process_name(name, tmp[0])
            continue
