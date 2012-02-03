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

import socket, select, threading

class ConsoleServer (threading.Thread):

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.clientsockets = []
        self.serversocket = None

    def run(self):
        try:
            self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serversocket.setblocking(0)
            self.serversocket.bind(("", self.port))
            self.serversocket.listen(5)
            self.keep_running = True

            while self.keep_running:
                s = select.select(self.clientsockets + [self.serversocket], [], [], 1)[0]
                for i in s:
                    if i is self.serversocket:
                        newclient = i.accept()[0]
                        newclient.setblocking(0)
                        self.clientsockets.append(newclient)
                    else:
                        try:
                            line = ""
                            while True:
                                char = i.recv(1)
                                if char in ("\r", "\n"):
                                    if len(line) is not 0: break
                                else:
                                    line += char
                            line = line.decode("utf-8")
                            self.line_received_callback(self, line)
                        except socket.error:
                            i.close()
                            self.clientsockets.remove(i)
        except:
            self.close()

    def send_line(self, line):
        for i in self.clientsockets:
            try:
                i.send(line.encode("utf-8") + "\n")
            except socket.error:
                i.close()
                self.clientsockets.remove(i)

    def set_line_received_callback(self, callback):
        self.line_received_callback = callback

    def close(self):
        self.serversocket.shutdown(socket.SHUT_RDWR)
        self.serversocket.close()
        for i in self.clientsockets:
            i.shutdown(socket.SHUT_RDWR)
            i.close()
        self.keep_running = False

