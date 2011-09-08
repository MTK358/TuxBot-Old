from irc import IrcClient
import xkcd
import man
import re
import sys
import time
import random
import os

server = "irc.esper.net"
port = 6667
channel = "#Linux"
nick = "TuxBot"
realname = "The #Linux Bot, development version"
datafile = os.environ["HOME"] + "/tuxbotfile"

commandref='''!help <key> -- get help about <key>
!sethelp <key>: <value> -- set what !help shows when given <key>
!man <section> <name> -- get the URL to an online man page
!synopsis <section> <name> -- get the SYNOPSIS section of the specified man page
!man <criteria> -- search for an online man page
!xkcd -- get a link to a random xkcd comic
!xkcd <number> -- get the link to the specified xkcd
!xkcd-linux -- get a random xkcd comic that mentions Linux
!xkcd-linux add <number> -- add a comic the the list used by "!xkcd-linux"
(Note: you can use "geek" instead of "linux" in the above two commands for geeky comics)
!time -- show the current time
!time <strftime> -- show the current time, with custom formatting. See "man strftime" for more.
(Note: you can use "date" instead of "time" in the above two commands)
!quit -- make TuxBot quit'''

def process_line(line, sender):
    line = line.strip()
    if len(line) == 0:
        return

    if line[0] == "!":
        # !sethelp <key>: <value> -- set what the !help command returns when given a certain key
        match = re.match(r'!sethelp\s+([^:]+):(.*)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            save_to_file("help-"+key, value)
            irc.send_message("Help for \"%s\" is now set to \"%s\"." % (key, value))
            return
        # !help <key> -- get help
        match = re.match(r'!help\s+(.*)$', line)
        if match:
            key = match.group(1)
            text = get_from_file("help-"+key)
            if text:
                irc.send_message("%s" % (text))
            else:
                irc.send_message("I don't have an answer for \"%s\". You can set it using the \"!sethelp question: answer\" command." % (key))
            return
        match = re.match(r'!help$', line)
        if match:
            irc.send_private_notice(commandref, sender)
            return

        # !man <section> <name> -- get the URL to an online man page
        match = re.match(r'!man\s+(\w+)\s+(\w+)$', line)
        if match:
            irc.send_message(man.get(match.group(1), match.group(2)))
            return
        # !synopsis <section> <name> -- print the "SYNOPSIS" section of the specified man page
        match = re.match(r'!synopsis\s+(\w+)\s+(\w+)$', line)
        if match:
            text = man.synopsis(match.group(1), match.group(2))
            if not text:
                irc.send_message("Failed to get man page for \"%s\" in section \"%s\"" % (match.group(2), match.group(1)))
                return
            irc.send_message(text)
            return
        # !man <criteria> -- search for an online man page
        match = re.match(r'!man\s+(\w+)$', line)
        if match:
            irc.send_message(man.search(match.group(1)))
            return

        match = re.match(r'!xkcd$', line)
        if match:
            irc.send_message(xkcd.get_random())
            return
        match = re.match(r'!xkcd\s+([0-9]+)$', line)
        if match:
            irc.send_message(xkcd.get_url(int(match.group(1))))
            return
        match = re.match(r'!xkcd-linux$', line)
        if match:
            l = file_get_all("xkcd-linux")
            if len(l) == 0:
                irc.send_message("No linux-related comics in list.")
            else:
                irc.send_message(xkcd.get_url(int(l[random.randint(0, len(l)-1)])))
            return
        match = re.match(r'!xkcd-linux\s+add\s+([0-9]+)$', line)
        if match:
            l = save_to_file("xkcd-linux", match.group(1))
            irc.send_message("Added %s to Linux comics list." % (match.group(1)))
            return
        match = re.match(r'!xkcd-geek\s+add\s+([0-9]+)$', line)
        if match:
            l = save_to_file("xkcd-geek", match.group(1))
            irc.send_message("Added %s to geek comics list." % (match.group(1)))
            return

        match = re.match(r'!(time|date)$', line)
        if match:
            irc.send_message(time.strftime("%A %Y-%m-%d %H:%M:%S %Z"))
            return
        match = re.match(r'!(time|date)\s+([^\s].*)$', line)
        if match:
            irc.send_message(time.strftime(match.group(2)))
            return

        # !quit -- make TuxBot quit
        match = re.match(r'!quit$', line)
        if match:
            irc.quit("Segmentation fault")
            time.sleep(3)
            sys.exit(0)
            return

        irc.send_message("Invalid command.")

    else:

        match = re.match(r'.*(i (hate|don\'?t like) tuxbot|tuxbot is (stupid|dumb|useless)).*', line)
        if match:
            irc.send_message("Shut up!")

def get_from_file(key):
    f = open(datafile, "r")
    value = None
    while True:
        line = f.readline()
        if len(line) == 0:
            break
        if line.find(key + ":") == 0:
            value = line[len(key)+1:]
    f.close()
    return value

def file_get_all(key):
    f = open(datafile, "r")
    l = []
    while True:
        line = f.readline()
        if len(line) == 0:
            break
        if line.find(key + ":") == 0:
            l.append(line[len(key)+1:])
    f.close()
    return l

def save_to_file(key, value):
    value.replace("\r", "")
    value.replace("\n", " ")
    f = open(datafile, "a")
    f.write(key + ":" + value + "\n")
    f.close()

irc = IrcClient(server, port, nick, realname)
joined = False

while True:
    # get input from the server
    string = irc.read()
    # iterate over the lines individually
    for line in string.split("\r\n"):
        print line

        # respond to PING commands
        tmp = irc.is_ping(line)
        if tmp:
            irc.send_pong(tmp)
            continue

        if not joined and line == ":"+nick+" MODE "+nick+" :+i":
            irc.join(channel)
            joined = True

        if not joined:
            continue

        # respond to posts on the channel
        tmp = irc.is_message(line)
        if tmp and tmp[1] == channel:
            process_line(tmp[2], tmp[0])

