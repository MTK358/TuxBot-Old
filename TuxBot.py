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

import irc
from configfile import ConfigFile
import misc
import datetime, getpass, os, random, re, select, signal, sys, time

if len(sys.argv) != 2:
    print "Usage: " + sys.argv[0] + " path/to/config/file"
    sys.exit(1)
config = ConfigFile(sys.argv[1])

pipe = os.popen('git log --pretty=format:"git commit %h (%s)"')
version = pipe.readline().strip()
pipe.close()

commandref = u'''!help <key> -- get help about <key>
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

opcommandref = u'''!quit -- make TuxBot quit
!reload-config -- reload the comfiguration file'''

license = u'''Copyright (C) 2011 Colson, LinuxUser324, Krenair and Tobias "ToBeFree" Frei.
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


def process_command_message(line, cmd):
    # !help -- get help about TuxBot's commads
    match = re.match(r'help$', line)
    if match:
        cmd.client.send_notice(commandref, cmd.hostmask.nick)
        if cmd.client.get_channel_info(cmd.args[0]).get_member(cmd.hostmask.nick).mode.contains("o"):
            cmd.client.send_notice(opcommandref, cmd.hostmask.nick)
        return True

    # !help <key> -- get help
    match = re.match(r'help\s+(.*)$', line)
    if match:
        key = match.group(1)
        if key in config.contents["help"]:
            cmd.client.send_message(config.contents["help"][key], cmd.args[0])
        else:
            cmd.client.send_message(u"I don't have an answer for \"%s\"." % (key), cmd.args[0])
        return True

    # !man <section> <name> -- get the URL to an online man page
    match = re.match(r'man\s+(\w+)\s+([-A-Za-z0-9_]+)$', line)
    if match:
        cmd.client.send_message(misc.get_man_page(match.group(1), match.group(2)), cmd.args[0])
        return True
    # !synopsis <section> <name> -- print the "SYNOPSIS" section of the specified man page
    match = re.match(r'synopsis\s+(\w+)\s+(\w+)$', line)
    if match:
        text = misc.get_man_page_synopsis(match.group(1), match.group(2))
        if not text:
            cmd.client.send_message(u"Failed to get man page for \"%s\" in section \"%s\"" % (match.group(2), match.group(1)), cmd.args[0])
            return True
        cmd.client.send_message(text, cmd.args[0])
        return True
    # !man <criteria> -- search for an online man page
    match = re.match(r'man\s+(\w+)$', line)
    if match:
        cmd.client.send_message(misc.search_man_page(match.group(1)), cmd.args[0])
        return True

    # !xkcd -- get a random xkcd comic
    match = re.match(r'xkcd$', line)
    if match:
        cmd.client.send_message(misc.get_random_xkcd(), cmd.args[0])
        return True
    # !xkcd <index> -- get an xkcd comic by index
    match = re.match(r'xkcd\s+([0-9]+)$', line)
    if match:
        cmd.client.send_message(misc.get_xkcd_url(int(match.group(1))), cmd.args[0])
        return True

    # !xkcd-linux and !xkcd-geek -- get linux-related and geeky xkcd comics
    match = re.match(r'xkcd-linux$', line)
    if match:
        cmd.client.send_message(misc.get_xkcd_url(random.choice(config.contents["xkcd"]["linux"])), cmd.args[0])
    match = re.match(r'xkcd-geek$', line)
    if match:
        cmd.client.send_message(misc.get_xkcd_url(random.choice(config.contents["xkcd"]["geek"])), cmd.args[0])
        return True

    # !google <criteria> -- get the URL for a Google search
    match = re.match(r'google\s+([^\s].+)$', line)
    if match:
        cmd.client.send_message(u"https://encrypted.google.com/#q=" + clean_string(match.group(1)).replace(" ", "+"), cmd.args[0])
        return True

    # !wikipedia -- get a random wikipedia article
    match = re.match(r'wikipedia$', line)
    if match:
        cmd.client.send_message(u"http://en.wikipedia.org/wiki/Special:Random", cmd.args[0])
        return True
    # !wikipedia <article> -- get a link to wikipedia article
    match = re.match(r'wikipedia\s+([^\s].+)$', line)
    if match:
        cmd.client.send_message(u"http://en.wikipedia.org/wiki/Special:Search?search=" + clean_string(match.group(1)).replace(" ", "+"), cmd.args[0])
        return True
    # !wikipedia-<lang> -- get a random wikipedia article in a certain language
    match = re.match(r'wikipedia-(\w+)$', line)
    if match:
        cmd.client.send_message(u"http://"+match.group(1)+".wikipedia.org/wiki/Special:Random", cmd.args[0])
        return True
    # !wikipedia-<lang> <article> -- get a link to wikipedia article in a certain language
    match = re.match(r'wikipedia-(\w+)\s+([^\s].+)$', line)
    if match:
        cmd.client.send_message(u"http://"+match.group(1)+".wikipedia.org/wiki/Special:Search?search=" + clean_string(match.group(2)).replace(" ", "+"), cmd.args[0])
        return True

    # !time and !date -- get the current time
    match = re.match(r'(time|date)$', line)
    if match:
        cmd.client.send_message(time.strftime("%A %Y-%m-%d %H:%M:%S %Z"), cmd.args[0])
        return True
    match = re.match(r'(time|date)\s+([^\s].*)$', line)
    if match:
        cmd.client.send_message(time.strftime(match.group(2)), cmd.args[0])
        return True

    # !tr[anslate]-<fromlang> <text> -- translate some text to English
    match = re.match(r'tr(anslate)?-([a-z]+)\s+([^\s].*)', line)
    if match:
        cmd.client.send_message(misc.translate(match.group(2), "en", match.group(3)), cmd.args[0])
        return True;

    # !tr[anslate]-<fromlang>-<tolang> <text> -- translate some text
    match = re.match(r'tr(anslate)?-([a-z]+)-([a-z]+)\s+([^\s].*)', line)
    if match:
        cmd.client.send_message(misc.translate(match.group(2), match.group(3), match.group(4)), cmd.args[0])
        return True;

    # !license or !authors or !credits -- display license information and the names of the people who made TuxBot
    match = re.match(r'credits|authors|license$', line)
    if match:
        cmd.client.send_notice(license, sender)
        return True

    # !user -- display the username which this python script is running under
    match = re.match(r'user$', line)
    if match:
        cmd.client.send_message(getpass.getuser(), cmd.args[0])
        return True

    # !version -- get TuxBot's version. Assumes that TuxBot is run from its git repository directory
    match = re.match(r'version$', line)
    if match:
        cmd.client.send_message(version, cmd.args[0])
        return True

    # !quit -- make TuxBot quit
    match = re.match(r'quit$', line)
    if match:
        if cmd.client.get_channel_info(cmd.args[0]).get_member(cmd.hostmask.nick).mode.contains("o"):
            raise QuitException()
            sys.exit(0)
        else:
            cmd.client.send_message(cmd.hostamsk.nick + ": Permission denied. You must be +o.", cmd.args[0])
        return True

    match = re.match(r'reload-config$', line)
    if match:
        if cmd.client.get_channel_info(cmd.args[0]).get_member(cmd.hostmask.nick).mode.contains("o"):
            config.reload()
        else:
            cmd.client.send_message(cmd.hostamsk.nick + ": Permission denied. You must be +o.", cmd.args[0])
        return True

    for i in config.contents["responses"]:
        if i[0] == "command":
            match = re.match(i[1] + "$", line)
            if match:
                run_action(i[2:], match, cmd)
                return True

    return False


def process_message(cmd):
    for command_prefix in config.contents["command-prefixes"]:
        match = re.match(command_prefix, cmd.args[1])
        if match and process_command_message(cmd.args[1][len(match.group(0)):], cmd):
            return
    if cmd.args[1][0] == "!":
        if process_command_message(cmd.args[1][1:], cmd):
            return
    for i in config.contents["responses"]:
        if i[0] == "message":
            match = re.match(i[1] + "$", cmd.args[1])
            if match:
                run_action(i[2:], match, cmd)
                break


def run_action(action, match, cmd):
    if action[0] == "message":
        if type(action[1]).__name__ == "list":
            cmd.client.send_message(match.expand(random.choice(action[1])), cmd.args[0])
        else:
            cmd.client.send_message(match.expand(action[1]), cmd.args[0])
    elif action[0] == "command":
        process_command_message(match.expand(action[1]), cmd)
    elif action[0] == "tempban":
        cmd.client.tempban(cmd.args[0], cmd.hostmask.nick, action[1][0], action[1][1])


flood_data = {}

def flood_check(cmd):
    sender = cmd.hostmask.nick
    channel = cmd.args[0]
    message = cmd.args[1]

    # don't respond to private messages
    if channel == cmd.client.nick:
        return
    idstr = channel + " " + sender
    found = False
    for i in flood_data.keys():
        # delete entries older than the timeout period
        if flood_data[i]["time"] < time.time() - config.contents["floodkick"]["time"]:
            del flood_data[i]
            continue
        # if this message was posted before by the same person less than the timeout period ago
        if i == idstr and len(message) <= config.contents["floodkick"]["maxlen"]:
            found = True
            count = flood_data[idstr]["count"] + 1
            if count >= config.contents["floodkick"]["count"]:
                client.send_line("KICK %s %s :Flooding" % (channel, sender))
                cmd.client.tempban(channel, sender, config.contents["floodkick"]["message"], config.contents["floodkick"]["bantime"])
                del flood_data[idstr]
            else:
                flood_data[idstr]["count"] = count
                flood_data[idstr]["time"] = time.time()
    if not found and len(message) <= 5:
        flood_data[idstr] = {"time": time.time(), "count": 1}


def signal_handler(signal, frame):
    on_quit()
signal.signal(signal.SIGINT, signal_handler)


def on_command_sent(client, line):
    print client.networkinfo["server"] + " < " + line


def on_quit():
    for i in clients:
        i.quit()
    sys.exit(0)


clients = []
for i in config.get_networks():
    j = irc.Client(i)
    j.connect()
    j.set_on_command_sent_callback(on_command_sent)
    clients.append(j)

inputstreams = [sys.stdin]
for i in clients:
    inputstreams.append(i.socket)

class QuitException:
    pass

try:
    while True:
        s = select.select(inputstreams, [], [])[0]
        
        if sys.stdin in s:
            line = sys.stdin.readline()
            match = re.match(r'(\*|[a-zA-Z0-9]+) +([^ ].*)', line)
            if match:
                prefix, line = match.group(1), match.group(2)
                if prefix is "*":
                    for client in clients:
                        client.send_line(line)
                else:
                    for client in clients:
                        abbrev = client.networkinfo["abbreviation"]
                        if prefix == abbrev or (len(prefix) < len(abbrev) and prefix == abbrev[:len(prefix)]):
                            client.send_line(line)
            continue

        for i in clients:
            if i.socket not in s: continue

            cmd = i.read_command()
            if not cmd.is_valid:
                continue

            print i.networkinfo["server"] + " > " + cmd.line

            sender = re.match(r'([^\s]+)', cmd.hostmask.string)
            if sender:
                sender = sender.group(1)
                ignore = False
                for ignore_pattern in i.networkinfo["ignore"]:
                    if re.match(ignore_pattern, sender):
                        ignore = True

            if cmd.command == "PRIVMSG" and not ignore:
                process_message(cmd)
                flood_check(cmd)
except QuitException:
    on_quit()

