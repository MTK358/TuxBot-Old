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

import socket
import re
import time

class IrcClient:

    def __init__(self, server, port, nick, realname):
        self.server = server
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server, port))
        self.set_nick(nick)
        self.socket.send("USER %s 8 * :%s\r\n" % (nick, realname))

    def readline(self):
        line = ""
        try:
            while True:
                line += self.socket.recv(1)
                if len(line) >= 2 and line[-2:] == "\r\n":
                    break
            return line.strip()
        except KeyboardInterrupt:
            pass

    def set_nick(self, nick):
        self.socket.send("NICK %s\r\n" % (nick))

    def join(self, channel):
        self.socket.send("JOIN %s\r\n" % (channel))
        self.current_channel = channel

    def send_message(self, message, to):
        first = True
        for line in message.split("\n"):
            if not first:
                time.sleep(0.3)
            self.socket.send("PRIVMSG "+to+" :"+line+"\r\n")
            first = False

    def send_private_notice(self, message, nick):
        first = True
        for line in message.split("\n"):
            if not first:
                time.sleep(0.3)
            self.socket.send("NOTICE "+nick+" :"+line+"\r\n")
            first = False

    def send_kick(self, channel, nick, message = ""):
        self.socket.send("KICK %s %s %s\r\n" % (channel, nick, message))

    def send_pong(self, message):
        self.socket.send("PONG :%s\r\n" % (message))

    def quit(self, message = ""):
        self.socket.send("QUIT :%s\r\n" % message)
        self.socket.close()

    def is_message(self, string):
        match = re.match(r':([^!]+)[^\s]+ PRIVMSG ([^\s]+) :(.*)', string)
        if match:
            return match.group(1), match.group(2), match.group(3)
        return None

    def is_ping(self, string):
        match = re.match(r'PING :(.*)', string)
        if match:
            return match.group(1)
        return None

    def is_quit(self, string):
        match = re.match(r':([^!]+)[^\s]+ QUIT( :(.*)|)', string)
        if match:
            return match.group(1), match.group(3)
        return None

    def is_kick(self, string):
        match = re.match(r':([^!]+)[^\s]+ KICK ([^\s]+) ([^\s]+)( (.*)|)', string)
        if match:
            return match.group(1), match.group(2), match.group(3), match.group(5)
        return None

    def is_part(self, string):
        match = re.match(r':([^!]+)[^\s]+? PART ([^\s]+)( :(.+)|)$', string)
        if match:
            return match.group(1), match.group(2), match.group(4)
        return None

    def is_mode(self, string):
        match = re.match(r':([a-zA-Z@!\.]+) MODE ([^\s]+) (.+)$', string)
        if match:
            modes = []
            setter = match.group(1)
            to = match.group(2)
            split = match.group(3).split(" ")
            if split[0][0] == ":":
                split[0] = split[0][1:] #if first character is ":", remove it
            paramindex = 1
            for mode in split[0]:
                if mode is "+":
                    give = True
                elif mode is "-":
                    give = False
                elif mode in ["q", "a", "o", "h", "v", "b", "e", "l"]:
                    modes.append(ModeSet(setter, to, mode, give, split[paramindex]))
                    paramindex += 1
                else:
                    modes.append(ModeSet(setter, to, mode, give))
            return modes
        return None
    
    def is_names(self, string):
        split = string.split(' ')
        if split[1] == '353':
            names = split[4:]
            names[1] = names[1][1:]
            return names
        return None

class ModeSet:
    def __init__(self, setter, to, mode, given, nick = None):
        self.setter = setter
        self.to = to
        self.mode = mode
        self.given = given
        self.nick = nick
