import queue
import socket
import selectors
from threading import Thread
import pyaudio
import struct


class NodeClient (Thread):
    def __init__(self, name, host="127.0.0.1", port=31257):
        Thread.__init__(self)
        # Network components
        self._host = host
        self._port = port
        self._listening_socket = None
        self._sock = None
        self._selector = selectors.DefaultSelector()
        self._name = name
        self._running = True
        self._token = None

        # for streaming
        self._streaming = False
        self._audio = pyaudio.PyAudio()
        self._stream = None

        # used to reconnect if any faults happen
        self._lastAddress = None
        self._primeNode = None

        # user authentication components
        self._userName = None
        self._token = None

        self._outgoing_buffer = queue.Queue()

        addr = (host, port)
        print("starting connection to", addr)

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setblocking(False)
        self._sock.connect_ex(addr)

        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self._selector.register(self._sock, events, data=None)

    def kill_connection(self):
        self._running = False

    def switchconnection(self, processtype, host, port, key):          # used for closing current connection of client
        newCon = {'type': processtype,  # and then it calls a method to connect to a new
                  'host': host,  # process or server
                  'port': port}

        oldCon = {'type': 'old',
                  'host': self._host,
                  'port': str(self._port)}

        self._lastAddress = oldCon

        print("closing connection", repr(key))
        self._selector.unregister(self._sock)
        self._sock.close()

        self.newconnection(newCon)

    def newconnection(self, address):               # this is called by the switch connection method and passes a
        self._sock = None                           # process object to give the client a new connection to connect to
        host = address['host']
        port = int(address['port'])
        addr = (host, port)
        print(addr)

        print("starting connection to", addr)

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setblocking(False)
        self._sock.connect_ex(addr)

        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self._selector.register(self._sock, events, data=None)

    def run(self):
        print("\033[94m" + f"entered run on {self._name}" + "\033[0m")
        try:
            while self._running:
                events = self._selector.select(timeout=1)
                for key, mask in events:
                    if mask & selectors.EVENT_READ:
                        self._read(key)
                    if mask & selectors.EVENT_WRITE and not self._outgoing_buffer.empty():
                        self._write(key)
                # Check for a socket being monitored to continue.
                if not self._selector.get_map():
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self._selector.close()

    def _read(self, key):
        if self._streaming:
            header_size = struct.calcsize("I")
            data = b""

            while True:
                try:
                    while len(data) < header_size:

                        packet = self._sock.recv(4096)  # 4K

                        if not packet:
                            break

                        data += packet

                    msg_size = struct.unpack("I", data[:header_size])[0]
                    data = data[header_size:]
                    print(data)

                    while len(data) < msg_size:
                        data += self._sock.recv(4096)

                    self._stream.write(data[:msg_size])

                    data = data[msg_size:]

                except socket.error as a:
                    self._streaming = False
                    print("Streaming Complete... Type 'list' to list other sounds you can stream or 'logout' to signout.")
                    break
        else:
            print("\033[94m" + f"entered read on {self._name}" + "\033[94m")
            recv_data = self._sock.recv(1024).decode()
            if recv_data:
                print("\033[94m" + "received", repr(recv_data), "from connection",
                      repr(key.fileobj.getpeername()) + "\033[94m\n")
                if recv_data.split(',')[0] == 'connect':  # connect is the trigger word to switch connection
                    print(recv_data)
                    connection = recv_data.split(',')
                    self.switchconnection(connection[1], connection[2], connection[3], key)
                elif recv_data.split(',')[0] == 'play':
                    print(recv_data)
                    data = recv_data.split(',')
                    self._stream = self._audio.open(
                        format=self._audio.get_format_from_width(2),
                        channels=int(data[1]),
                        rate=int(data[2]),
                        output=bool(data[3]),
                        frames_per_buffer=int(data[4])
                    )
                    self._streaming = True
                elif recv_data == 'loggedin?':
                    if self._token is None:
                        self.postmessage('notLoggedIn')
                    else:
                        print(self._token)
                        self.postmessage(str(self._token))
                elif recv_data == 'type??':
                    self.postmessage('client')
                elif recv_data.split(':')[0] == 'token':
                    recv_data = recv_data.split(':')
                    self._userName = recv_data[2]
                    self._token = recv_data[1]
                elif recv_data == 'removCache':
                    self._token = None
                    self._userName = None

            if not recv_data:
                print("closing connection", repr(key))
                self._selector.unregister(self._sock)
                self._sock.close()

    def _write(self, key):
        print("\033[94m" + f"entered write on {self._name}" + "\033[0m")
        try:
            message = self._outgoing_buffer.get_nowait()
        except queue.Empty:
            message = None
        if message:
            sent = self._sock.send(message.encode())

    def postmessage(self, message):
        self._outgoing_buffer.put(message)
