import multiprocessing
import subprocess
import NodeServer
import socket
import random


class Node:
    def __init__(self, host="127.0.0.1", port=12345):   # The host should be set to the address of
        # self._host = self.get_host_ip_address()       # the computer the node is running on.
        self._host = "127.0.0.1"
        self._port = port
        self._type = 'node'
        self._node = None

        self._primeHost = "127.0.0.1"      # set primePort and primeHost to whatever the address
        self._primePort = 50000            # the first node you run is on


    # Node class creates a prime node when the node if the first to be started
    def createprimenode(self):
        server = NodeServer.NodeServer(self._primeHost, self._primePort)
        server.start()
        self._node = server
        self._node._type = 'prime'

    # Creates regular node when there is already a prime node
    def createnormalnode(self):
        self._port = self.getrandomport()
        server = NodeServer.NodeServer(self._host, self._port)
        server.start()
        self._node = server
        self._node.PRIME = False
        print(str(self._port))
        self.registernode()

    # called when initializing the server to create extra processors
    def createprocess(self, file, port, servicetype, message):
        process1 = multiprocessing.Process(target=self.subprocess(file, port, message), daemon=True)
        process1.start()
        self._node.addaddress(servicetype, self._host, port)       # passes addresses to NodeServer Class

    # called by multiprocessing.Process. it creates a process
    def subprocess(self, file, port, message):
        file = "services/" + file
        prime = 'prime:' + self._primeHost + ':' + str(self._primePort)
        subprocess.Popen(["Python", "{}".format(file), port, self._host, prime, message])

    # Checks whether a prime node is already running
    def testforconnection(self):
        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = a_socket.connect_ex((self._primeHost, self._primePort))
        a_socket.close()
        if result == 0:
            self.createnormalnode()
        else:
            self.createprimenode()

    # registers a node with the prime node
    def registernode(self):
        s = socket.socket()  # Create a socket object
        s.connect((self._primeHost, self._primePort))
        message = 'node:' + self._host + ':' + str(self._port)
        s.sendall(message.encode())
        message = s.recv(1024)
        message = message.decode()
        s.close()

        if message == 'ok':
            print('Registered Correctly')
            print(self._type)
        else:
            print('Not registered Correctly')
            print(message)
        self.loopforservices()


    # Regular nodes continually loop to see if they have been told to start up a service
    def loopforservices(self):
        while True:
            if self._node.startService:
                service = self._node.startService[0]
                print('SELF: Starting service -> ' + service)
                self.createprocess(service, str(self.getrandomport()), service.split('.')[0], 'none')
                self._node.startService.pop(0)

            if self._node.startLoadBalancer:
                balancer = self._node.startLoadBalancer[0]['type']
                message = self._node.startLoadBalancer[0]['message']
                loadBType = balancer.split('.')[0] + '-' + message.split(':')[0]
                print('SELF: Starting service -> ' + loadBType)
                self.createprocess(balancer, str(self.getrandomport()), loadBType, message)
                self._node.startLoadBalancer.pop(0)


    # Uses recursion to get a port which is not in use
    def getrandomport(self):
        port = random.randint(50000, 50050)
        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = a_socket.connect_ex((self._host, port))
        a_socket.close()
        if result == 0:
            return self.getrandomport()
        else:
            return port


    def get_host_ip_address(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Use Google Public DNS server to determine own IP
        sock.connect(('8.8.8.8', 80))
        local_ip = sock.getsockname()[0]
        return local_ip

if __name__ == "__main__":
    node = Node()
    node.testforconnection()
