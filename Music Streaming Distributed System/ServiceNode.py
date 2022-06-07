import struct
import time

if __name__ == "__main__":
    import socket
    import sys
    import threading
    import wave

    primeNode = ''
    loadBalancer = False
    connections = 0

    root = "./sounds/"
    files = ['example', 'thunder', 'police', 'jaildoor']

    fileDetails = [{'name': 'example',
                    'channels': '2',
                    'rate': '11025',
                    'output': 'True',
                    'frames': '4096'
                    },
                   {'name': 'thunder',
                    'channels': '2',
                    'rate': '22050',
                    'output': 'True',
                    'frames': '4096'
                    },
                   {'name': 'jaildoor',
                    'channels': '2',
                    'rate': '22050',
                    'output': 'True',
                    'frames': '4096'
                    },
                   {'name': 'police',
                    'channels': '2',
                    'rate': '22050',
                    'output': 'True',
                    'frames': '4096'
                    }]

    def handle(peer_socket: socket.socket) -> None:

        global connections
        global loadBalancer

        try:
            received_data = peer_socket.recv(4096).decode()
            print(received_data)

            while received_data:
                if received_data == 'connectionsnow?':
                    connections = connections - 1
                    peer_socket.send(str(connections).encode("utf-8"))
                    loadBalancer = True
                    break
                elif received_data == 'logout':
                    peer_socket.send('removCache'.encode("utf-8"))
                    time.sleep(1)

                    address = askforaddr(primeNode, 'ControlNode')
                    address = address.split(':')
                    message = 'connect,' + address[0] + ',' + address[1] + ',' + address[2]
                    connections -= 1
                    peer_socket.send(message.encode("utf-8"))
                    break

                if received_data in files:
                    details = detailbuilder(received_data)

                    peer_socket.send(details.encode("utf-8"))

                    file = received_data + ".wav"
                    print('streaming')
                    with wave.open(root + file, 'rb') as waveform:
                        chunk_size = 4096
                        chunk_data = waveform.readframes(chunk_size)
                        while chunk_data:
                            peer_socket.send(struct.pack("I", len(chunk_data)) + chunk_data)
                            chunk_data = waveform.readframes(chunk_size)
                elif received_data == 'list':
                    string = "Files Available:"
                    for a in files:
                        string = string + " " + a + ", "
                    peer_socket.send(string.encode("utf-8"))
                    peer_socket.send(f"Type a file name to stream it".encode("utf-8"))
                else:
                    peer_socket.send(f"'{received_data}' is not a correct command".encode("utf-8"))

                received_data = peer_socket.recv(4096).decode()
        except:
            connections -= 1
            print('User Disconnected')

    def listen() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            global primeNode
            global connections
            global loadBalancer

            server_port = int(sys.argv[1])
            server_host = sys.argv[2]
            primeNode = handleprime()
            registerself(primeNode, server_host, server_port)

            # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((server_host, server_port))
            server_socket.listen()

            while True:
                peer_socket, address = server_socket.accept()
                peer_socket.send(b"Type 'list' to list the files available for streaming. Type 'logout' to sign out.")

                connections += 1
                if connections == 3:
                    if not loadBalancer:
                        registerasfull(primeNode, server_host, server_port)
                        loadBalancer = True

                threading.Thread(target=handle, args=[peer_socket]).start()

    def detailbuilder(file):
        for a in fileDetails:
            if file == a['name']:
                return 'play,' + a['channels'] + ',' + a['rate'] + ',' + a['output'] + ',' + a['frames']

    def handleprime():
        parent = sys.argv[3].split(':')
        parentNode = {'type': parent[0],
                      'host': parent[1],
                      'port': int(parent[2])}
        return parentNode

    def askforaddr(prime, processtype):
        message = 'address:' + processtype
        return sendmessage(prime, message)

    def registerasfull(addr, host, port):
        message = 'max:ServiceNode:' + host + ':' + str(port)
        sendmessage(addr, message)

    def registerself(prime, host, port):
        message = 'service:' + 'ServiceNode:' + host + ':' + str(port)
        sendmessage(prime, message)

    def sendmessage(addr, message):
        s = socket.socket()
        s.connect((addr['host'], addr['port']))
        s.sendall(message.encode())
        returnMessage = s.recv(1024).decode()
        return returnMessage

    print("Service Node : " + str(sys.argv[2]) + ':' + sys.argv[1])
    threading.Thread(target=listen).start()
