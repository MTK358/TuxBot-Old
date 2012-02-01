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

opcommandref = '''!quit -- make TuxBot quit
!reload-config -- reload the comfiguration file'''

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


server, port = config.get_server()
nick = config.get_nick()
realname = config.get_realname()

def clean_string(string):
    return re.sub("\s+", " ", re.sub("[^-_\w\s]", "", string.lower()))


def process_command_message(line, cmd):
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
            irc.send_message("I don't have an answer for \"%s\"." % (key), channel)
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

    # !google <criteria> -- get the URL for a Google search
    match = re.match(r'google\s+([^\s].+)$', line)
    if match:
        irc.send_message("https://encrypted.google.com/#q=" + clean_string(match.group(1)).replace(" ", "+"), channel)
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

    # !tr[anslate]-<fromlang> <text> -- translate some text to English
    match = re.match(r'tr(anslate)?-([a-z]+)\s+([^\s].*)', line)
    if match:
        irc.send_message(translator.translate(match.group(2), "en", match.group(3)), channel)
        return True;

    # !tr[anslate]-<fromlang>-<tolang> <text> -- translate some text
    match = re.match(r'tr(anslate)?-([a-z]+)-([a-z]+)\s+([^\s].*)', line)
    if match:
        irc.send_message(translator.translate(match.group(2), match.group(3), match.group(4)), channel)
        return True;

    # !license or !authors or !credits -- display license information and the names of the people who made TuxBot
    match = re.match(r'credits|authors|license$', line)
    if match:
        irc.send_private_notice(license, sender)
        return True

    # !user -- display the username which this python script is running under
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

    response = config.get_command_response(clean_string(line))
    if response:
        irc.send_message(response.replace("\\s", sender), channel)
        return
    response = config.get_command_response_command(clean_string(line))
    if response:
        process_command(response, sender, channel)
        return

    return False


def process_message(cmd):
    for command_prefix in command_prefixes:
        match = re.match(command_prefix, line)
        if match and process_command_message(line[len(match.group(0)):], cmd):
            return
    response = config.get_response(clean_string(line))
    if response:
        irc.send_message(response.replace("\\s", sender), to)
        return
    response = config.get_response_command(clean_string(line))
    if response:
        process_command(response, cmd)
        return


flood_data = {}

def flood_check(channel, sender, message):
    # don't respond to private messages
    if channel == nick:
        return
    idstr = channel + " " + sender
    found = False
    for i in flood_data.keys():
        # delete entries older than the timeout period
        if flood_data[i]["time"] < time.time() - 2:
            del flood_data[i]
            continue
        # if this message was posted before by the same person less than the timeout period ago
        if i == idstr and len(message) <= 5:
            found = True
            count = flood_data[idstr]["count"] + 1
            if count >= 5:
                irc.send_kick(channel, sender, "Flooding")
                del flood_data[idstr]
            else:
                flood_data[idstr]["count"] = count
                flood_data[idstr]["time"] = time.time()
    if not found and len(message) <= 5:
        flood_data[idstr] = {"time": time.time(), "count": 1}


def op_config_ops(channel, hostmask):
    if not client.get_channel_info(channel).get_member_info(hostmask.nick).mode.contains("o"):
        irc.send_command("MODE %s +o %s" % (channel, hostmask.nick));


def process_mode(cmd):
    if len(cmd.args) >= 3:
        op_config_ops(cmd.args[0], cmd.hostmask)


def process_join(cmd):
    op_config_ops(cmd.args[0], cmd.hostmask)


def signal_handler(signal, frame):
    client.quit(config.get_quitmessage())
    print ''
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


client = irc.Client()
joined = False
def on_command_sent(line):
    print "> " + line
client.set_on_command_sent_callback(on_command_sent)

client.connect(server, port, nick, realname)

while True:
    s = select.select([client.socket, sys.stdin], [], [])[0]
    if sys.stdin in s:
        client.send_line(sys.stdin.readline().strip() + "\r\n")

    if client.socket in s:
        cmd = client.read_command()
        if not cmd.is_valid:
            continue

        print cmd.line

        sender = re.match(r'([^\s]+)', cmd.hostmask.string)
        if sender:
            sender = sender.group(1)
            ignore = False
            #for ignore_pattern in config.get_ignores():
                #if re.match(ignore_pattern, sender):
                    #ignore = True

        if cmd.command == "PRIVMSG" and not ignore:
            process_message(cmd)
            flood_check(cmd)
        elif cmd.command == "JOIN":
            process_join(tmp[0], tmp[1])
        elif cmd.command == "MODE":
            process_mode(cmd)


