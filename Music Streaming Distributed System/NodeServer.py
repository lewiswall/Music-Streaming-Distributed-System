import NodeServerThread
import socket
import selectors
from threading import Thread

class NodeServer (Thread):
    def __init__(self, host="127.0.0.1", port=31100):
        Thread.__init__(self)
        # Network components
        self._host = host
        self._port = port
        self._type = 'node'             #used in nodeServerThread to split the message system up
        self._listening_socket = None
        self._selector = selectors.DefaultSelector()
        self.PRIME = True       #used to test if the node is the prime node in NodeServerThread

        # Client Threads
        self._modules = []

        # Addresses of control nodes and service nodes
        self._nodes = []
        self._addresses = []

        # Used by Node class to set up new services
        self._startService = []

        # Used by Prime Node to set up servers
        self.AUTH = False
        self.DICT = False

    def _configureServer(self):
        self._listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Avoid bind() exception: OSError: [Errno 48] Address already in use
        self._listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listening_socket.bind((self._host, self._port))
        self._listening_socket.listen()

        print("listening on", (self._host, self._port))
        self._listening_socket.setblocking(False)
        self._selector.register(self._listening_socket, selectors.EVENT_READ, data=None)

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print("accepted connection from", addr)

        conn.setblocking(False)
        module = NodeServerThread.NodeServerThread(conn, addr, self)    # passes itself so the client threads can communicate with each other
        self._modules.append(module)
        module.start()

    def addProcess(self, type, address, port):
        # this is going to be called by the node class when starting new processors.
        # it will pass the self._processors module the type, address and port number of new processors
        process = {'type': type,
                   'host': address,
                   'port': port}
        if(process['type'] == 'node'):
            self._nodes.append(process)
            print(self._nodes)
        else:
            self._addresses.append(process)
            print(self._addresses)

    def pullProcessors(self, type):     # used by server threads to pull a certain type of processors
        processors = []                 # used to pass connections to clients
        for a in self._addresses:
            if a['type'] == type:
                processors.append(a)
        return processors

    def pullAllProcessors(self):        # used by the Node class to pull every process to pass to a load balancer
        return self._addresses

    def AddToBuffer(self, message):
        pass

    def PullFromBuffer(self):
        pass

    def run(self):
        self._configureServer()

        try:
            while True:
                events = self._selector.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                       pass
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            self._selector.close()