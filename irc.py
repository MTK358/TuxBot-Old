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

import re, socket, time, ssl, eventloop

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

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)
        

class Command:

    def __init__(self, line, time, client):
        self.line = line
        self.client = client

        match = re.match(r'(:([^\s]+) )?([A-Za-z0-9]+)( .+)?$', line)

        self.is_valid = match != None
        if not self.is_valid:
            return

        self.time = time

        # hostmask
        if match.group(2):
            self.hostmask = Hostmask(match.group(2))
        else:
            self.hostmask = Hostmask("!%s" % client.nick)

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
        if len(self.args) == 2 and len(self.args[1]) >= 2 and self.args[1][0] == "\x01" and self.args[1][-1] == "\x01" and (self.command == "PRIVMSG" or self.command == "NOTICE"):
            if self.command == "PRIVMSG":
                self.command = "CTCP"
            else:
                self.command = "CTCPREPLY"

            self.args[1] = self.args[1][1:-1]

            index = self.args[1].find(" ")
            if index != -1:
                self.args.append(self.args[1][index+1:])
                self.args[1] = self.args[1][:index]
            
            self.args[1] = self.args[1].upper()

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)


# TODO it might just be better to store modes as strings, and to have a function this applies one mode string to another
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
            self.negative = False
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
                    self.string += newmode.string[i]
    
    def contains(self, char):
        return self.string.find(char) != -1

    def contains_any(self, chars):
        for char in chars:
            if self.string.find(char) != -1: return True
        return False


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

    def __init__(self, evloop, networkinfo):
        self.networkinfo = networkinfo
        self.command_sent_callbacks = []
        self.command_received_callbacks = []
        self.ping_timer = None
        self.welcome_timer = None
        self.ping_status = ""
        self.tempban_timers = []
        self.evloop = evloop
        self.linebuf = ""
        self.noreconnect = False
        # default nick prefixes, in case the server doesn't say
        self.nickprefixes = ("qaohv", "~&@%+")
        self.connected = False

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.networkinfo["ssl"]:
            self.socket = ssl.wrap_socket(self.socket)
        self.evloop.socket(self.socket, self.on_socket_readyread, self.on_socket_ex)

    def on_connected(self):
        print 'connected'
        self.connected = True
        self.nick = self.networkinfo["identity"]["nick"]
        self.send_cmd(u"NICK %s" % (self.networkinfo["identity"]["nick"]))
        self.send_cmd(u"USER %s 8 * :%s" % (self.networkinfo["identity"]["username"], self.networkinfo["identity"]["realname"]))
        self.nick = self.networkinfo["identity"]["nick"]
        self.mode = Mode()
        self.channelinfos = []

    def on_socket_readyread(self):
        print 'readyread'
        if not self.connected:
            self.on_connected()

        if not self.socket: return

        c = self.socket.recv(1)
        if c == "" or not c:
            self.connected = False
            self.evloop.cancel_timer(self.ping_timer)
            self.evloop.cancel_timer(self.welcome_timer)
            self.socket.close()
            if not self.noreconnect: self.evloop.timer(5, self.connect)

        while True:
            if c == "\r" or c == "\n":
                try:
                    self.linebuf = self.linebuf.decode("utf-8")
                except:
                    self.linebuf = self.linebuf.decode("iso-8859-15")
                cmd = Command(self.linebuf, self.nick, self)
                if cmd.is_valid:
                    self._process_incoming_command(cmd)
                self.linebuf = ""
            else:
                self.linebuf = self.linebuf + c
            c = self.socket.recv(1)
            if c == "" or not c: break

    def on_socket_ex(self):
        print 'ex'
        self.connected = False
        self.socket.close()
        self.evloop.cancel_timer(self.ping_timer)
        self.evloop.cancel_timer(self.welcome_timer)
        if not self.noreconnect: self.evloop.timer(5, self.connect)

    def on_disconnected(self):
        print 'discon'
        self.connected = False
        self.evloop.cancel_timer(self.ping_timer)
        self.evloop.cancel_timer(self.welcome_timer)
        if not self.noreconnect: self.evloop.timer(5, self.connect)

    def ping(self):
        self.evloop.cancel_timer(self.ping_timer)
        self.ping_status = "TuxBot" # "TuxBot" is just a random string here, it doesn't mean anything
        self.send_cmd("PING TuxBot")
        self.ping_timer = self.evloop.timer(15, self.on_ping_timeout)


    def on_ping_timeout(self):
        self.socket.close()
        if not self.noreconnect: self.evloop.timer(5, self.connect)

    def on_welcome_timer(self):
        print 'welcome timer'
        self.socket.close()
        self.evloop.timer(5, self.connect)

    def set_on_command_sent_callback(self, callback):
        self.on_command_sent_callback = callback

    def send_cmd(self, line, callbackinfo = None):
        for i in self.command_sent_callbacks: i(self, line, callbackinfo)
        self.socket.send(line.encode("utf-8") + "\r\n")

    def connect(self):
        self.noreconnect = False
        self.socket.connect((self.networkinfo["server"], self.networkinfo["port"]))
        self.welcome_timer = self.evloop.timer(45, self.on_welcome_timer)

    def tempban(self, channel, nick, reason, timeout):
        hostmask = self.get_channel_info(channel).get_member(nick).hostmask.host
        if hostmask:
            hostmask = "*!*@" + hostmask
        else:
            hostmask = nick + "!*@*"
        self.send_cmd("MODE %s +b %s" % (channel, hostmask))
        self.send_cmd("KICK %s %s :%s (Temporary ban, %i seconds)" % (channel, nick, reason, timeout))
        timer = self.evloop.timer(timeout, self.on_tempban_timeout, [channel, hostmask])
        self.tempban_timers.append(timer)

    def on_tempban_timeout(self, chanandhostmask):
        self.send_cmd("MODE %s -b %s" % chanandhostmask)
        self.tempban_timers.remove(timer)

    def send_msg(self, message, to, callbackinfo = None):
        first = True
        for line in message.split("\n"):
            if not first:
                time.sleep(1)
            self.send_cmd(u"PRIVMSG " + to + " :" + line, callbackinfo)
            first = False
            
    def send_ctcp(self, to, cmd, arg = None):
        if arg:
            message = "%s %s" % (cmd, arg)
        else:
            message = cmd
        self.send_cmd(u"PRIVMSG %s :\001%s\001" % (to, message))
    
    def send_ctcpreply(self, to, cmd, arg = None):
        if arg:
            message = "%s %s" % (cmd, arg)
        else:
            message = cmd
        self.send_cmd(u"NOTICE %s :\001%s\001" % (to, message))

    def send_notice(self, message, nick):
        first = True
        for line in message.split("\n"):
            if not first:
                time.sleep(1)
            self.send_cmd(u"NOTICE " + nick + " :" + line)
            first = False

    def send_kick(self, channel, nick, message = ""):
        self.send_cmd(u"KICK %s %s %s" % (channel, nick, message))

    def quit(self, message = None):
        self.noreconnect = True
        if message == None:
            message = self.networkinfo["identity"]["quitmessage"]
        self.send_cmd(u"QUIT :%s" % (message))
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

    def _process_incoming_command(self, cmd):
        for i in self.command_received_callbacks: i(cmd)

        if cmd.command == "JOIN" and len(cmd.args) >= 1:
            if areIrcNamesEqual(cmd.hostmask.nick, self.nick):
                self.channelinfos.append(ChannelInfo(cmd.args[0]))
            chan = self.get_channel_info(cmd.args[0])
            if chan: chan.members.append(MemberInfo(cmd.hostmask))

        elif cmd.command == "PART" and len(cmd.args) >= 1:
            if areIrcNamesEqual(cmd.hostmask.nick, self.nick):
                self.remove_channel_info(cmd.args[0])
            else:
                chan = self.get_channel_info(cmd.args[0])
                if chan: chan.remove_member(cmd.hostmask.nick)

        elif cmd.command == "KICK" and len(cmd.args) >= 2:
            if areIrcNamesEqual(cmd.args[1], self.nick):
                self.remove_channel_info(cmd.args[0])
            else:
                chan = self.get_channel_info(cmd.args[0])
                if chan: chan.remove_member(cmd.args[1])

        elif cmd.command == "NICK" and len(cmd.args) >= 1:
            if areIrcNamesEqual(cmd.hostmask.nick, self.nick):
                self.nick = cmd.args[0]
            for channel in self.channelinfos:
                member = channel.get_member(cmd.hostmask.nick)
                if member:
                    member.hostmask.nick = cmd.args[0]
            
        elif cmd.command == "QUIT":
            if areIrcNamesEqual(cmd.hostmask.nick, self.nick):
                pass
                # XXX do something
            else:
                for channel in self.channelinfos:
                    channel.remove_member(cmd.hostmask.nick)

        elif cmd.command == "MODE" and len(cmd.args) >= 2:
            if areIrcNamesEqual(cmd.args[0], self.nick):
                self.mode.change(Mode(cmd.args[1]))
            else:
                chan = self.get_channel_info(cmd.args[0])
                if chan and len(cmd.args) >= 3:
                    if len(cmd.args[1]) >= 2 and len(cmd.args) == len(cmd.args[1]) + 1:
                        for i in range(1, len(cmd.args[1])):
                            member = chan.get_member(cmd.args[i + 1])
                            if member:
                                member.mode.change(Mode("%s%s" % (cmd.args[1][0], cmd.args[1][i])))
                    else:
                        for i in range(1, len(cmd.args), 2):
                            member = chan.get_member(cmd.args[i + 1])
                            if member:
                                member.mode.change(Mode(cmd.args[i]))

        elif cmd.command == "353" and len(cmd.args) >= 4: # NAMES reply
            channelinfo = self.get_channel_info(cmd.args[2])
            if channelinfo:
                for i in cmd.args[3].split(" "):
                    prefixindex = self.nickprefixes[1].find(i[0])
                    if prefixindex != -1:
                        mode = Mode(self.nickprefixes[0][prefixindex])
                        nick = i[1:]
                    else:
                        nick = i
                        mode = Mode()
                    channelinfo.members.append(MemberInfo(Hostmask("!%s" % (nick)), mode))

        elif cmd.command == "001": # WELCOME reply
            for i in self.networkinfo["autorun"]:
                self.send_cmd(i)
            self.ping_status = ""
            self.evloop.cancel_timer(self.welcome_timer)
            self.ping()

        elif cmd.command == "005":
            match = re.match(r'PREFIX=\(([^ ]+)\)([^ ]+)', cmd.line)
            if match:
                self.nickprefixes = (match.group(1), match.group(2))

        elif cmd.command == "PONG" and len(cmd.args) >= 2:
            if cmd.args[1] == self.ping_status:
                self.ping_status = ""
                self.evloop.cancel_timer(self.ping_timer)
                self.ping_timer = self.evloop.timer(90, self.ping)

        elif cmd.command == "PING":
            if len(cmd.args) >= 1:
                self.send_cmd(u"PONG :%s" % cmd.args[0])
            else:
                self.send_cmd("PONG")
        
