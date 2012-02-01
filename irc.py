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

import re, socket, time

def areIrcNamesEqual(a, b):
    return a.lower() == b.lower() # FIXME

class Hostmask:

    def __init__(self, string):
        match = re.match(r'(.+)!(.+)@(.+)$', string)
        if match:
            self.nick = match.group(1);
            self.username = match.group(2);
            self.host = match.group(3);
            self.string = string
        elif string[0] == "!": # special syntax for creating a hostmask with just a nick
            self.nick = string[1:]
            self.username = None
            self.host = None
            self.string = ""
        else:
            self.nick = None
            self.username = None
            self.host = string
            self.string = string


class Command:

    def __init__(self, line, client_nick, time):
        self.line = line

        match = re.match(r'(:([^\s]+) )?([A-Za-z0-9]+)( .+)?$', line)

        self.is_valid = match != None
        if not self.is_valid:
            return

        self.time = time

        # hostmask
        if match.group(2):
            self.hostmask = Hostmask(match.group(1))
        else:
            self.hostmask = Hostmask("!%s" % client_nick)

        # command type
        self.command = match.group(3).upper()

        # arguments
        argstr = match.group(4)
        if argstr:
            index = argstr.find(" :")
            if index != -1:
                self.args = argstr[:index].split(" ")
                self.args = filter(lambda i: i, self.args)
                self.args.append(argstr[index+2:])
            else:
                self.args = argstr.split(" ")
                self.args = filter(lambda i: i, self.args)

        # CTCP
        if len(self.args) == 2 and self.args[1][0] == "\x01" and self.args[1][-1] == "\x01" and (self.command == "PRIVMSG" or self.command == "NOTICE"):

            if self.command == "PRIVMSG":
                self.command = "CTCP"
            else:
                self.command = "CTCPREPLY"

            self.args[1] = self.args[1:-2]

            index = self.args[1].find(" ")
            if index != -1:
                self.args.append(self.args[1][index+1:])
                self.args[1] = self.args[1][:index]


class Mode:

    def __init__(self, string = ""):
        if not string:
            self.negative = False
            self.string = ""
        elif string[0] == "+":
            self.negative = False
            self.string = string[1:]
        elif string[0] == "-":
            self.negative = True
            self.string = string[1:]
        else:
            self.string = string

    # assumes that "self" is not negative
    def change(self, newmode):
        for i in range(0, len(newmode.string)):
            if newmode.string[i] in self.string:
                if newmode.negative:
                    index = self.string.find(newmode.string[i])
                    self.string = self.string[:index] + self.string[index+1:]
            else:
                if not newmode.negative:
                    self.string.append(newmode.string[i])


class MemberInfo:

    def __init__(self, hostmask, mode = Mode("")):
        self.hostmask = hostmask
        self.mode = mode
        
class ChannelInfo:

    def __init__(self, name, mode = Mode("")):
        self.name = name;
        self.mode = mode;
        self.members = []

    def get_member(self, nick):
        for i in self.members:
            if areIrcNamesEqual(i.hostmask.nick, nick):
                return i

    def remove_member(self, nick):
        for i in range(0, len(self.members)):
            if areIrcNamesEqual(self.members[i].hostmask.nick, nick):
                del self.members[i]
                break


class Client:

    def __init__(self):
        self.on_command_sent_callback = None
        self.nick = ""
        self.mode = Mode()
        self.channelinfos = []

    def set_on_command_sent_callback(self, callback):
        self.on_command_sent_callback = callback

    def send_line(self, line):
        if self.on_command_sent_callback: self.on_command_sent_callback(line)
        self.socket.send(line + "\r\n")

    def connect(self, server, port, nick, realname):
        self.server = server
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server, port))
        self.send_line("NICK %s" % (nick))
        self.send_line("USER %s 8 * :%s" % ("TuxBot", realname))

    def read_command(self):
        line = ""
        try:
            while True:
                line += self.socket.recv(1)
                if len(line) >= 2 and line[-2:] == "\r\n":
                    break
            line = line.strip()
            com = Command(line, time, self.nick)
            if com.is_valid:
                self.process_incoming_command(com)
            return com
        except KeyboardInterrupt:
            pass

    def send_message(self, message, to):
        first = True
        for line in message.split("\n"):
            if not first:
                time.sleep(1)
            self.send_line("PRIVMSG " + to + " :" + line)
            first = False

    def send_notice(self, message, nick):
        first = True
        for line in message.split("\n"):
            if not first:
                time.sleep(1)
            self.send_line("NOTICE " + nick + " :" + line)
            first = False

    def send_kick(self, channel, nick, message = ""):
        self.send_line("KICK %s %s %s" % (channel, nick, message))

    def quit(self, message = ""):
        self.send_line("QUIT :%s" % (message))
        self.socket.close()

    def get_channel_info(self, channel):
        for i in self.channelinfos:
            if areIrcNamesEqual(channel, i.name):
                return i
        
    def remove_channel_info(self, channel):
        for i in range(0, len(self.channelinfos)):
            if areIrcNamesEqual(self.channelinfos[i].name, channel):
                del self.channelinfos[i]
                break

    def process_incoming_command(self, com):
        if com.command == "JOIN":
            if areIrcNamesEqual(com.hostmask.nick, self.nick):
                self.channelinfos.append(ChannelInfo(com.args[0]))
            self.get_channel_info(com.args[0]).members.append(MemberInfo(com.hostmask))

        elif com.command == "PART":
            if areIrcNamesEqual(com.hostmask.nick, self.nick):
                self.remove_channel_info(com.args[0])
            else:
                self.get_channel_info(com.args[0]).remove_member(com.hostmask.nick)

        elif com.command == "KICK":
            if areIrcNamesEqual(com.args[1], self.nick):
                self.remove_channel_info(com.args[0])
            else:
                self.get_channel_info(com.args[0]).remove_member(com.args[1])

        elif com.command == "NICK":
            if areIrcNamesEqual(com.hostmask.nick, self.nick):
                self.nick = com.args[0]
            for channel in self.channelinfos:
                channel.get_member(com.hostmask.nick).hostmask.nick = com.args[0]
            
        elif com.command == "QUIT":
            if areIrcNamesEqual(com.hostmask.nick, self.nick):
                pass
                # XXX do something
            else:
                for channel in self.channels:
                    self._remove_channel_member(channel, com.hostmask.nick)

        elif com.command == "MODE":
            if len(com.args) >= 3:
                channel_info = self.get_channel_info(com.args[0]).get_member_info(com.args[2]).mode.change(Mode(com.args[2]))
            elif areIrcNamesEqual(com.args[0], self.nick):
                self.mode.change(Mode(com.args[1]))

        elif com.command == "353":
            channelinfo = get_channel_info(com.args[2])
            for i in com.args[3].split(" "):
                if i[0] == "@":
                    nick = i[1:]
                    mode = Mode("+o")
                elif i[0] == "+":
                    nick = i[1:]
                    mode = Mode("+v")
                else:
                    nick = i
                    mode = Mode()
                channelinfo.members.append(MemberInfo(Hostmask("!%s" % (nick)), mode))

        elif com.command == "PING":
            self.send_line("PONG :%s" % com.args[0])
            

