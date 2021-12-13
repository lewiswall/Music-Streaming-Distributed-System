import multiprocessing
import subprocess
import NodeServer
import socket
import random

class Node:
    def __init__(self, host="127.0.0.1", port=12345):   # The host should be set to the address of the computer the node is running on.
        self._host = host
        self._port = port
        self._type = 'node'
        self._node = None

        self._primeHost = "127.0.0.1"      # set primePort and primeHost to whatever the address
        self._primePort = 12345            # the first node you run is on

    def createPrimeNode(self):
        server = NodeServer.NodeServer(self._host, self._port)
        server.start()
        self._node = server
        self._node._type = 'prime'
        self.createProcess('ServiceNode.py', str(self.getRandomPort()), 'ServiceNode')

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
        prime = 'prime:' + self._host + ':' + str(self._primePort)
        subprocess.Popen(["Python", "{}".format(file), port, self._host, prime])

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
        s.connect((self._primeHost, self._primePort))
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
                pass
            else:
                service = self._node._startService[0]
                print('SELF: Starting service -> ' + service)
                self.createProcess(service, str(self.getRandomPort()), service.split('.')[0])
                self._node._startService.pop(0)


    def getRandomPort(self):
        return random.randint(10000, 30000)

    def run(self):
        self.testForConnection()

if __name__ == "__main__":
    node = Node()
    node.run()
