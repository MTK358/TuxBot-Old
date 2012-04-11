
import time, select

class EventLoop:

    def __init__(self):
        self.timers = {}
        self.sockets = []
        self.socketcallbacks = []
        self.next_timer_id = 0
        self.next_timer = None
        self.exiteventloop = False

    def socket(self, socket, on_readyread, on_ex):
        self.sockets.append(socket)
        self.socketcallbacks.append((on_readyread, on_ex))

    def remove_socket(self, socket):
        for i in range(len(self.sockets)):
            if self.sockets[i] == socket:
                del self.sockets[i]
                del self.socketcallbacks[i]
                return

    def timer(self, timeout, callback, arg = None):
        tid = self.next_timer_id
        self.next_timer_id = self.next_timer_id + 1
        self.timers[tid] = (time.time() + timeout, callback, arg)
        return tid

    def cancel_timer(self, tid):
        try:
            del self.timers[tid]
        except KeyError:
            pass

    def exit(self):
        self.exiteventloop = True

    def _time_to_next_timer(self):
        if len(self.timers) == 0:
            self.next_timer = None
            return None

        t = None
        for tid, i in self.timers.iteritems():
            if t:
                if i[0] < t:
                    t = i[0]
                    self.next_timer = tid
            else:
                t = i[0]
                self.next_timer = tid
        if not t: return None
        t = t - time.time()
        if t < 0: t = 0
        return t

    def run(self):
        while True:
            rlist, _, xlist = select.select(self.sockets,
                                            [],
                                            self.sockets, 
                                            self._time_to_next_timer())
            if len(rlist) == 0 and len(wlist) == 0 and len(xlist) == 0:
                if self.next_timer and self.timers.contains(self.next_timer):
                    self.timers[self.next_timer][1](self.timers[self.next_timer][2])
                    del self.timers[self.next_timer]
            else:
                for i in range(len(self.sockets)):
                    if self.sockets[i] in rlist:
                        if(self.socketcallbacks[i][0]): self.socketcallbacks[i][0]()
                    if self.sockets[i] in xlist:
                        if(self.socketcallbacks[i][1]): self.socketcallbacks[i][1]()

            if self.exiteventloop:
                self.exiteventloop = False
                break

