import socket
import sys
import threading
import time

connections = 0
primeNode = ''
loadBalancer = False

hostport = ''
logins = []
tokens = []


def handle(peer_socket: socket.socket) -> None:
    global primeNode
    global connections
    global loadBalancer
    global logins
    global tokens
    global hostport

    tokenAccepted = False
    correctUser = None

    try:
        received_data = peer_socket.recv(4096).decode()
        while received_data:

            if received_data == 'connectionsnow?':
                connections = connections - 1
                peer_socket.send(str(connections).encode("utf-8"))
                loadBalancer = True
                break
            elif received_data.split(':')[0] == 'usertoken':
                connections -= 1
                received_data = received_data.split(':')
                login = {'user': received_data[1],
                         'token': received_data[2]}

                logins.append(login)
                tokens.append(received_data[2])

                break
            elif received_data == '#info#':
                connections = connections - 1
                message = str(logins) + ';' + str(tokens)
                peer_socket.send(message.encode("utf-8"))
                break

            if not tokenAccepted:
                if received_data == 'notLoggedIn':
                    peer_socket.send(f"Would you like to login or signup? send 'l' to login or"
                                     f" 's' to signup.".encode("utf-8"))
                elif received_data == 's' or received_data == 'S':
                    connections -= 1
                    signup = askforaddr(primeNode, 'SignUp').split(':')
                    message = 'connect,' + signup[0] + ',' + signup[1] + ',' + signup[2]
                    peer_socket.send(message.encode("utf-8"))
                elif received_data == 'l' or received_data == 'L':
                    connections -= 1
                    address = askforaddr(primeNode, 'Login').split(':')
                    message = 'connect,' + address[0] + ',' + address[1] + ',' + address[2]
                    peer_socket.send(message.encode("utf-8"))
                elif received_data in tokens:
                    for user in logins:
                        if received_data == user['token']:
                            tokenAccepted = True
                            correctUser = user
                            peer_socket.send('Token Accepted. Please Re-enter your username.'.encode("utf-8"))
                else:
                    peer_socket.send(f"Incorrect Command. If you have already logged in an error may have occured,"
                                     f" Please type 'l' to log back in.".encode("utf-8"))

            else:
                if received_data == correctUser['user']:
                    connections -= 1
                    peer_socket.send('Username Accepted. Redirecting to Music Service...'.encode("utf-8"))
                    time.sleep(1)

                    serviceNode = askforaddr(primeNode, 'ServiceNode').split(':')
                    message = 'connect,' + serviceNode[0] + ',' + serviceNode[1] + ',' + serviceNode[2]

                    peer_socket.send(message.encode("utf-8"))

                else:
                    peer_socket.send('Username Not Accepted. Please use the username you '
                                     'used to login.'.encode("utf-8"))

            received_data = peer_socket.recv(4096).decode()
    except:
        connections -= 1
        print('User Disconnected unexpectedly')


def listen() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        global connections
        global primeNode
        global loadBalancer
        global hostport

        server_port = int(sys.argv[1])
        server_host = sys.argv[2]
        hostport = '[CONTROL NODE : ' + str(server_host) + ' - ' + str(server_port) + ']'
        primeNode = handleprime()
        requestinfo()

        registerself(primeNode, server_host, server_port)

        # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((server_host, server_port))
        server_socket.listen()

        while True:
            peer_socket, address = server_socket.accept()

            peer_socket.send(f'loggedin?'.encode("utf-8"))

            connections = connections + 1  # This part is to register that this node/service is full at 3 cons

            if connections == 3:
                if not loadBalancer:
                    registerasfull(primeNode, server_host, server_port)
                    loadBalancer = True

            threading.Thread(target=handle, args=[peer_socket]).start()


def handleprime():
    global primeNode

    prime = sys.argv[3].split(':')
    primeNode = {'type': prime[0],
                 'host': prime[1],
                 'port': int(prime[2])}
    return primeNode


def requestinfo():
    global logins
    global tokens

    message = 'addrs:ControlNode'
    addresses = sendmessage(primeNode, message)           # returns another login address from prime node
    addresses = eval(addresses)
    # address = addresses[0]
    #
    # if address['host'] == sys.argv[2]:
    #     if address['port'] == sys.argv[1]:
    #         addresses = []

    if not addresses:
        pass
    else:
        address = addresses[0]
        message = '#info#'
        s = socket.socket()
        s.connect((address['host'], int(address['port'])))
        s.sendall(message.encode())
        returnMessage = s.recv(1024).decode()
        returnMessage = s.recv(1024).decode()

        returnMessage = returnMessage.split(';')
        logins = eval(returnMessage[0])
        tokens = eval(returnMessage[1])


def registerself(prime, host, port):
    message = 'service:' + 'ControlNode:' + host + ':' + str(port)
    sendmessage(prime, message)


def askforaddr(prime, processtype):
    message = 'address:' + processtype
    return sendmessage(prime, message)


def registerasfull(addr, host, port):
    message = 'max:ControlNode:' + host + ':' + str(port)
    sendmessage(addr, message)


def sendmessage(addr, message):
    s = socket.socket()
    s.connect((addr['host'], addr['port']))
    s.sendall(message.encode())
    returnMessage = s.recv(1024).decode()
    s.close()
    return returnMessage



print('ControlNode STARTED : ' + str(sys.argv[2]) + ':' + sys.argv[1])

if __name__ == "__main__":
    threading.Thread(target=listen).start()
