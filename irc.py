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

    def read(self):
        return self.socket.recv(4096)

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

