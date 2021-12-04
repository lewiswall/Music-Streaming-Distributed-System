import multiprocessing
import subprocess
import NodeServer
import socket
import random

class Node:
    def __init__(self, host="127.0.0.1", port=31259):
        self._host = host
        self._port = port
        self._type = 'node'
        self._node = None

    def createPrimeNode(self):
        server = NodeServer.NodeServer(self._host, self._port)
        server.start()
        self._node = server
        self._node._type = 'prime'
        self.createProcess('ServiceNode.py', str(self.getRandomPort()), 'service')

        #just a way to retrieve host computers ip address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(local_ip)

    def createNormalNode(self):
        self._port = self.getRandomPort()
        server = NodeServer.NodeServer(self._host, self._port)
        server.start()
        self._node = server
        self._node.PRIME = False
        self.registerNode()

    def createProcess(self, file, port, type):              # called when initializing the server to create extra processors
        process1 = multiprocessing.Process(target=self.subProcess(file, port), daemon=True)
        process1.start()
        self._node.addProcess(type, self._host, port)       # passes addresses to NodeServer Class

    def subProcess(self, file, port):           # called by multiprocessing.Process. it creates a process
        parent = 'parent:' + self._host + ':' + str(self._port)
        subprocess.Popen(["Python", "{}".format(file), port, parent])


    def testForConnection(self):
        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = a_socket.connect_ex((self._host, self._port))
        a_socket.close()
        if result == 0:
            self.createNormalNode()
        else:
            self.createPrimeNode()


    #registers a node with the prime node
    def registerNode(self):
        s = socket.socket()  # Create a socket object
        s.connect(('127.0.0.1', 31259))
        message = 'node:' + self._host + ':' + str(self._port)
        s.sendall(message.encode())
        message = s.recv(1024)
        message = message.decode()

        if(message == 'ok'):
            print('Registered Correctly')
            print(self._type)
        else:
            print('Not registered Correctly')
            print(message)
        self.loopForServices()

    def loopForServices(self):
        while True:
            if not self._node._startService:
                print('empty')
            else:
                print('starting service')


    def getRandomPort(self):
        return random.randint(10000, 30000)

    def run(self):
        self.testForConnection()

if __name__ == "__main__":
    node = Node()
    node.run()













"""
    A node will represent any item in our distributed system.

    It should be capable of:
        accepting incoming connections on a known port (NodeServer.py)
        processing data from that server (NodeServerThread.py)

        Creating connections to other Servers (NodeClient.py)

        We will likely need specialised variants of these - at the moment they just echo data.

        Tasks:
            Step 1: Create a combined node class that can create servers and clients
            Step 2: The node should default to a known address, checking for the existance of a prime node
            Step 3: If there is a prime node, create a client to server connection to it, register ourselves
            Step 4: Add some kind of functionality to create server/clients on demand
                prime node sends "CREATE SERVER 127.0.0.1 12345"
                prime node sends "CONNECT 127.0.0.1 12345"
                prime node sends "RECONNECT AUTHSERVER 127.0.0.1 12345"
                etc.
            Step 5: Create a few simple specialised node classes e.g.
                echoNode
                pingNode
                etc. (these will later replace their functionality with something sensible)

"""