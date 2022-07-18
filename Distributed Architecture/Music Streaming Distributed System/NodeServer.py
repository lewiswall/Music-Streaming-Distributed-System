import NodeServerThread
import socket
import selectors
from threading import Thread
import random


class NodeServer (Thread):
    def __init__(self, host="127.0.0.1", port=31100):
        Thread.__init__(self)
        # Network components
        self._host = host
        self._port = port
        self._type = 'node'             # used in nodeServerThread to split the message system up
        self._listening_socket = None
        self._selector = selectors.DefaultSelector()
        self.PRIME = True       # used to test if the node is the prime node in NodeServerThread

        self._processStarted = False

        # Client Threads
        self._modules = []

        # Addresses of control nodes and service nodes
        self.nodes = []
        self.addresses = []

        # Used by Node class to set up new services
        self.startService = []
        self.startLoadBalancer = []

        # Used by Prime Node to set up servers
        self._services = ['SignUp.py', 'Login.py', 'ServiceNode.py', 'ControlNode.py']

        # Load balancer addresses
        self.loadBalancers = []

        # loadBalancer = {'type' : 'type',
        #                 'host' : host,
        #                 'port' : port}

        self.controlLoadBalancer = False
        self.signUpLoadBalancer = False
        self.loginLoadBalancer = False
        self.serviceLoadBalancer = False

    def _configureserver(self):
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
        # passes itself so the client threads can communicate with each other and the parent
        module = NodeServerThread.NodeServerThread(conn, addr, self)
        self._modules.append(module)
        module.start()

    def addaddress(self, servicetype, host, port):
        # this is going to be called by the node class when starting new processors.
        # it will pass the self._processors module the type, address and port number of new processors
        process = {'type': servicetype,
                   'host': host,
                   'port': port}
        if process['type'] == 'node':
            if process in self.nodes:
                pass
            else:
                self.nodes.append(process)
                print(self.nodes)
        else:
            if process in self.addresses:
                pass
            else:
                self.addresses.append(process)
                if self.PRIME:
                    self.checkloadbalancer(process)

    def checkloadbalancer(self, process):     # checks if a service registering with the prime node has a load balancer,
        processtype = process['type']         # if it does it will send the load balancers the address of the service

        if processtype == 'ControlNode':
            if self.controlLoadBalancer:
                self.sendtoloadbalancer(processtype, process)
        if processtype == 'SignUp':
            if self.signUpLoadBalancer:
                self.sendtoloadbalancer(processtype, process)
        if processtype == 'Login':
            if self.loginLoadBalancer:
                self.sendtoloadbalancer(processtype, process)
        if processtype == 'ServiceNode':
            if self.serviceLoadBalancer:
                self.sendtoloadbalancer(processtype, process)

    def sendtoloadbalancer(self, processtype, process):
        for a in self.loadBalancers:
            loadType = a['type'].split('-')[1]
            if loadType == processtype:
                self.messagetoloadb(a, str(process))

    def messagetoloadb(self, loadb, message):
        message = 'addr:' + message
        s = socket.socket()
        s.connect((loadb['host'], int(loadb['port'])))
        returnMessage = s.recv(1024).decode()
        s.sendall(message.encode())
        returnMessage = s.recv(1024).decode()
        print('PRIME:' + returnMessage)

    def pullprocessors(self, processtype):     # used by server threads to pull a certain type of processors
        processors = []                 # used to pass connections to clients
        for a in self.addresses:
            if a['type'] == processtype:
                processors.append(a)
        return processors

    def addloadbalancer(self, processtype, host, port):    # this sets the load balancer type varibales to true if one
        if processtype == 'ControlNode':                   # gets setup then it adds the load balancer addr to the array
            self.controlLoadBalancer = True
        elif processtype == 'SignUp':
            self.signUpLoadBalancer = True
        elif processtype == 'Login':
            self.loginLoadBalancer = True
        elif processtype == 'ServiceNode':
            self.serviceLoadBalancer = True

        processtype = 'LoadBalancer-' + processtype
        loadBalancer = {'type': processtype,
                        'host': host,
                        'port': port}

        if loadBalancer in self.loadBalancers:
            pass
        else:
            self.loadBalancers.append(loadBalancer)

    def pullloadbalancer(self, processtype):
        processors = []  # used to pass connections to clients
        for a in self.loadBalancers:
            if a['type'] == processtype:
                processors.append(a)

        randomNum = random.randint(0, len(processors) - 1)
        return processors[randomNum]

    def pullallprocessors(self):        # used by the Node class to pull every process to pass to a load balancer
        return self.addresses

    def run(self):
        self._configureserver()
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

    # This is called from a prime node thread. When 3 other nodes connect to it, it picks nodes at random to set up
    # the services in self._services.
    def startservices(self):
        i = 0
        while i < 4:
            randomNum = random.randint(0, len(self.nodes) - 1)
            node = self.nodes[randomNum]
            print(node)
            self.servicemessage(node, self._services[i])
            i += 1

    # This is called from startServices() and is used to send messages to the other nodes to start services
    def servicemessage(self, node, service):
        s = socket.socket()
        message = 'start:' + service
        s.connect((node['host'], int(node['port'])))
        s.sendall(message.encode())
        reply = s.recv(1024)
        reply = reply.decode()
        s.close()



    def startextraservices(self, service):
        i = 0
        while i < 1:
            randomNum = random.randint(0, len(self.nodes) - 1)
            node = self.nodes[randomNum]
            self.servicemessage(node, service)
            i += 1

    def startloadbalancers(self, processtype, servicehost, serviceport):
        i = 0
        message = 'LoadBalancer.py:' + processtype + ':' + servicehost + ':' + serviceport
        while i < 1:
            randomNum = random.randint(0, len(self.nodes) - 1)
            node = self.nodes[randomNum]
            self.servicemessage(node, message)
            i += 1
