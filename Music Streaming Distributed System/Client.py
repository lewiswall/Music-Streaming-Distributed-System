import NodeClient
import socket


class Client:
    def __init__(self, host="127.0.0.1", port=50000):
        self._host = host
        self._port = port
        self._type = 'C'
        self._node = None

    def createclient(self, clientname):
        clientnode = NodeClient.NodeClient(clientname, self._host, self._port)
        clientnode.start()
        self._node = clientnode

        primeAddr = {'host': self._host,
                     'port': str(self._port)}
        self._node._primeNode = primeAddr
        self._node.postmessage('new')

    def testforconnection(self):
        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = a_socket.connect_ex((self._host, self._port))
        a_socket.close()
        if result == 0:
            self.createclient("module1")

    def listenformessage(self):
        while True:
            userMessage = input("")
            self._node.postmessage(userMessage)

    def run(self):
        self.testforconnection()
        self.listenformessage()


if __name__ == "__main__":
    client = Client()
    client.run()
