import NodeClient
import socket

class Client:
    def __init__(self, host="127.0.0.1", port=12345):
        self._host = host
        self._port = port
        self._type = 'C'
        self._node = None

    def createClient(self, clientName):
        client = NodeClient.NodeClient(clientName, self._host, self._port)
        client.start()
        self._node = client

        primeAddr = {'host': self._host,
                     'port': str(self._port)}
        self._node._primeNode = primeAddr
        self._node.postMessage('new')

    def testForConnection(self):
        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = a_socket.connect_ex((self._host, self._port))
        a_socket.close()
        if result == 0:
            self.createClient("module1")

    def listenForMessage(self):
        while True:
            userMessage = input("")
            self._node.postMessage(userMessage)

    def run(self):
        self.testForConnection()
        self.listenForMessage()


if __name__ == "__main__":
    client = Client()
    client.run()
