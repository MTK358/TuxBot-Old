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
        self.buf = []

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

    def send_message(self, message, channel = None):
        if channel == None:
            channel = self.current_channel
        first = True
        for line in message.split("\n"):
            if not first:
                time.sleep(0.3)
            self.socket.send("PRIVMSG "+channel+" :"+line+"\r\n")
            first = False

    def send_private_notice(self, message, nick):
        first = True
        for line in message.split("\n"):
            if not first:
                time.sleep(0.3)
            self.socket.send("NOTICE "+nick+" :"+line+"\r\n")
            first = False

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
        match = re.match(r':([^!]+)[^\s]+ PART (.*)', string)
        if match:
            channels = []
            for channel in match.group(2).split(","):
                channels.append(channel)
            return match.group(1), channels
        return None

    def is_mode(self, string):
        match = re.match(r':([^!]+)[^\s]+ MODE ([^\s]+) (.*)', string)
        if match:
            setter = match.group(1)
            to = match.group(2)
            data = match.group(3)
            if "+" in data:
                index = data.find("+")
            elif "-" in data:
                index = data.find("-")
            else:
                index = data.find("+")
            index = data[index:].find(" ")
            nicks = data[index + 1:].split(" ")
            modes = data[:index]
            nickindex = 0
            give = None
            out = []
            for i in modes:
                if i is "+":
                    give = True
                elif i is "-":
                    give = False
                elif i in ["o", "v"] and give is not None:
                    out.append(ModeSet(setter, to, i, give, nicks[nickindex]))
                    nickindex += 1
            return out
        return None

class ModeSet:
    def __init__(self, setter, to, mode, given, nick = None):
        self.setter = setter
        self.to = to
        self.mode = mode
        self.given = given
        if nick is not None:
            self.nick = nick
