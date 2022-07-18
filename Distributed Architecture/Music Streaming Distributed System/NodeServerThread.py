import queue
import socket
import selectors
from threading import Thread


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

    def pullprocessors(self, processtype):                     # pull processors from NodeServer (parent of thread)
        processors = self.parent.pullprocessors(processtype)
        return processors

    def pulladdress(self, processtype):
        if self.parent.PRIME:
            if processtype == 'SignUp':
                if self.parent.signUpLoadBalancer:
                    address = self.parent.pullloadbalancer('LoadBalancer-SignUp')
                    message = address['type'] + ':' + address['host'] + ':' + address['port']
                    return message
                else:
                    address = self.pullprocessors(processtype)
                    address = address[0]
                    message = address['type'] + ':' + address['host'] + ':' + address['port']
                    return message
            elif processtype == 'ControlNode':
                if self.parent.controlLoadBalancer:
                    address = self.parent.pullloadbalancer('LoadBalancer-ControlNode')
                    message = address['type'] + ':' + address['host'] + ':' + address['port']
                    return message
                else:
                    address = self.pullprocessors(processtype)
                    address = address[0]
                    message = address['type'] + ':' + address['host'] + ':' + address['port']
                    return message
            elif processtype == 'Login':
                if self.parent.loginLoadBalancer:
                    address = self.parent.pullloadbalancer('LoadBalancer-Login')
                    message = address['type'] + ':' + address['host'] + ':' + address['port']
                    return message
                else:
                    address = self.pullprocessors(processtype)
                    address = address[0]
                    print(address)
                    message = address['type'] + ':' + address['host'] + ':' + address['port']
                    return message
            elif processtype == 'ServiceNode':
                if self.parent.serviceLoadBalancer:
                    address = self.parent.pullloadbalancer('LoadBalancer-ServiceNode')
                    message = address['type'] + ':' + address['host'] + ':' + address['port']
                    return message
                else:
                    address = self.pullprocessors(processtype)
                    address = address[0]
                    message = address['type'] + ':' + address['host'] + ':' + address['port']
                    return message

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

                # when 3 nodes register this will call a function from its parent(NodeServer) which sets up services
                if len(self.parent.nodes) >= 2 and not self.parent._processStarted and self.parent.PRIME:
                    self.parent._processStarted = True
                    print('Starting services')
                    if self.parent._processStarted:
                        self.parent.startservices()

        except KeyboardInterrupt:
            pass
        finally:
            self._selector.close()

    def _read(self, key):
        print("\033[92m" + f"entered read on {key.fileobj.getsockname()}" + "\033[0m")
        recv_data = self._sock.recv(1024).decode()
        if recv_data:
            print("received", repr(recv_data), "from connection", repr(key.fileobj.getpeername()))
            if recv_data == 'kill':
                print("closing connection", repr(key))
                self._selector.unregister(self._sock)
                self._sock.close()
            elif recv_data == 'new' and self.parent.PRIME:
                message = ''
                if self.parent.controlLoadBalancer:
                    address = self.parent.pullloadbalancer('LoadBalancer-ControlNode')
                    message = 'connect,' + address['type'] + ',' + address['host'] + ',' + address['port'] + ','
                else:
                    nodes = self.pullprocessors('ControlNode')
                    for a in nodes:
                        message = 'connect,' + a['type'] + ',' + a['host'] + ',' + a['port'] + ','
                self.postmessage(message)
            elif recv_data.split(':')[0] == 'node':
                node = recv_data.split(':')
                self.parent.addaddress('node', node[1], node[2])
                self.postmessage('ok')
            elif recv_data.split(':')[0] == 'start':
                self.postmessage('ok')
                if recv_data.split(':')[1] == 'LoadBalancer.py':
                    service = recv_data.split(':')[1]
                    message = recv_data.split(':')[2:]
                    message = ':'.join(message)

                    loadBalancer = {'type': service,
                                    'message': message}
                    self.parent.startLoadBalancer.append(loadBalancer)

                else:
                    service = recv_data.split(':')[1]
                    self.parent.startService.append(service)
            elif recv_data.split(':')[0] == 'service':
                service = recv_data.split(":")
                self.parent.addaddress(service[1], service[2], service[3])
                self.postmessage('ok')
            elif recv_data.split(':')[0] == 'address':
                address = self.pulladdress(recv_data.split(':')[1])
                self.postmessage(address)
            elif recv_data.split(':')[0] == 'max' and self.parent.PRIME:
                self.postmessage('ok')
                recv_data = recv_data.split(':')
                self.parent.startloadbalancers(recv_data[1], recv_data[2], recv_data[3])
            elif recv_data.split(':')[0] == 'LoadBalancer' and self.parent.PRIME:
                recv_data = recv_data.split(':')
                self.parent.addloadbalancer(recv_data[1], recv_data[2], recv_data[3])
                addrs = self.pullprocessors(recv_data[1])
                self.postmessage(str(addrs))
            elif recv_data.split(':')[0] == 'newService' and self.parent.PRIME:  # starts new service
                service = recv_data.split(':')[1]
                self.parent.startextraservices(service)
                self.postmessage('ok')
            elif recv_data.split(':')[0] == 'user':
                addresses = self.pullprocessors('Login')
                self.sendmessagetoserver(addresses, recv_data)
                self.postmessage('ok')
            elif recv_data.split(':')[0] == 'usertoken':
                loginAddrs = self.pullprocessors('Login')
                self.sendmessagetoserver(loginAddrs, recv_data)

                controlAddrs = self.pullprocessors('ControlNode')
                self.sendmessagetoserver(controlAddrs, recv_data)
                self.postmessage('ok')
            elif recv_data.split(':')[0] == 'addrs':
                recv_data = recv_data.split(':')
                addresses = self.pullprocessors(recv_data[1])
                self.postmessage(str(addresses))
            else:
                self.postmessage(recv_data)

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

    def postmessage(self, message):
        self._outgoing_buffer.put(message)

    def sendmessagetoserver(self, addresses, message):
        for a in addresses:
            s = socket.socket()
            s.connect((a['host'], int(a['port'])))
            s.sendall(message.encode())
            returnMessage = s.recv(1024).decode()
