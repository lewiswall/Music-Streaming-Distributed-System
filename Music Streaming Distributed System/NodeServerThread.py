import queue
import socket
import selectors
from threading import Thread
import types

class NodeServerThread (Thread):
    def __init__(self, sock, addr, parent):
        Thread.__init__(self)
        # Network components
        self._listening_socket = None
        self._sock = sock
        self._addr = addr
        self._selector = selectors.DefaultSelector()
        self._running = True
        self.parent = parent
        self._outgoing_buffer = queue.Queue()

        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self._selector.register(self._sock, events, data=None)

    def kill_connection(self):
        self._running = False

    def processBufferMessage(self, messsage):
        pass

    def pullProcessors(self, type):                     #pull processors from NodeServer (parent of thread)
        processors = self.parent.pullProcessors(type)
        return processors

    def run(self):
        print("\033[92m" + f"entered run on {self._sock.getsockname()}" + "\033[0m")
        try:
            while self._running:

                # Check for network messages
                events = self._selector.select(timeout=1)
                for key, mask in events:
                    if mask & selectors.EVENT_READ:
                        self._read(key)
                    if mask & selectors.EVENT_WRITE and not self._outgoing_buffer.empty():
                        self._write(key)
                # Check for a socket being monitored to continue.
                if not self._selector.get_map():
                    break

                # check internal buffers:
                if message := self.parent.PullFromBuffer():
                    self.processBufferMessage(message)

        except KeyboardInterrupt:
            pass
        finally:
            self._selector.close()

    def _read(self, key):
        print("\033[92m" + f"entered read on {key.fileobj.getsockname()}" + "\033[0m")
        recv_data = self._sock.recv(1024).decode()
        if recv_data:
            print("received", repr(recv_data), "from connection", repr(key.fileobj.getpeername()))
            if (recv_data == 'kill'):
                print("closing connection", repr(key))
                self._selector.unregister(self._sock)
                self._sock.close()
            elif(recv_data == 'new' and self.parent.PRIME):
                nodes = self.pullProcessors('service')
                for a in nodes:
                    message = 'connect,' + a['type'] + ',' + a['host'] + ',' + a['port'] + ','
                    self.postMessage(message)
            elif(recv_data.split(':')[0] == 'node'):
                node = recv_data.split(':')
                message = 'ok'
                self.parent.addProcess('node', node[1], node[2])
                self.postMessage(message)
            elif(recv_data == 'auth'):
                nodes = self.pullProcessors('auth')
                for a in nodes:
                    message = 'connect,' + a['type'] + ',' + a['host'] + ',' + a['port'] + ','
                    self.postMessage(message)
            else:
                self.postMessage(recv_data)

        if not recv_data:
            print("closing connection", repr(key))
            self._selector.unregister(self._sock)
            self._sock.close()

    def _write(self, key):
        print("\033[92m" + f"entered write on {key.fileobj.getsockname()}" + "\033[0m")
        try:
            message = self._outgoing_buffer.get_nowait()
        except queue.Empty:
            message = None
        if message:
            sent = self._sock.send(message.encode())

    def postMessage(self, message):
        self._outgoing_buffer.put(message)


    def sendMessageToServer(self, addresses, message):
        s = socket.socket()
        for a in addresses:
            s.connect((a['host'], int(a['port'])))
            s.sendall(message.encode())
            message = s.recv(1024)
            message = message.decode()
