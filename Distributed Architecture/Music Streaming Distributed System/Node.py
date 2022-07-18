import multiprocessing
import subprocess
import NodeServer
import socket
import random
import NodeFunctions


class Node:
    def __init__(self, host="127.0.0.1", port=12345):   # The host should be set to the address of
        # self._host = self.get_host_ip_address()       # the computer the node is running on.
        self._host = "127.0.0.1"
        self._port = self.getrandomport()
        self._type = 'node'
        self._node = None

        self._primeHost = "127.0.0.1"      # set primePort and primeHost to whatever the address
        self._primePort = 50000            # the first node you run is on


    # Checks whether a prime node is already running
    def testforconnection(self):
        if self.checkForCon(self._primePort, self._primeHost) == 0:
            self.createnormalnode()
        else:
            self.createprimenode()


    def createprimenode(self):
        self._node = self.createNode(self._primeHost, self._primePort)
        self._node._type = 'prime'


    def createnormalnode(self):
        self._node = self.createNode(self._host, self._port)
        self._node.PRIME = False
        self.registerNodeWithPrime()


    def createNode(self, host, port):
        server = NodeServer.NodeServer(host, port)
        server.start()
        return server


    def registerNodeWithPrime(self):
        msg = 'node:' + self._host + ':' + str(self._port)
        retMsg = NodeFunctions.SendMessage(self._primeHost, self._primePort, msg)

        if retMsg == 'ok':
            print('Node Registered Correctly')
        else:
            print('Node Not Registered Correctly')
            print(retMsg)
        self.loopForServices()

    # Regular nodes continually loop to see if they have been told to start up a service
    def loopForServices(self):
        while True:
            self.tryForService()
            self.tryForLoadBalancer()


    def tryForService(self):
        if self._node.startService:
            service = self._node.startService.pop(0)
            print('SELF: Starting service -> ' + service)
            self.createprocess(service, str(self.getrandomport()), service.split('.')[0], 'none')


    def tryForLoadBalancer(self):
        if self._node.startLoadBalancer:
            balancer = self._node.startLoadBalancer[0]['type']
            message = self._node.startLoadBalancer[0]['message']
            loadBType = balancer.split('.')[0] + '-' + message.split(':')[0]
            print('SELF: Starting service -> ' + loadBType)
            self.createprocess(balancer, str(self.getrandomport()), loadBType, message)
            self._node.startLoadBalancer.pop(0)


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





    # Uses recursion to get a port which is not in use
    def getrandomport(self):
        port = random.randint(50000, 50050)
        if self.checkForCon(port, self._host) == 0:
            return self.getrandomport()
        else:
            return port


    def checkForCon(self, port, host):
        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = a_socket.connect_ex((host, port))
        a_socket.close()
        return result


    def get_host_ip_address(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Use Google Public DNS server to determine own IP
        sock.connect(('8.8.8.8', 80))
        local_ip = sock.getsockname()[0]
        return local_ip

if __name__ == "__main__":
    node = Node()
    node.testforconnection()
