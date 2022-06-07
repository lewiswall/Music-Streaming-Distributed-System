import time

if __name__ == "__main__":
    import socket
    import sys
    import threading

    connections = 0
    primeNode = ''
    loadBalancer = False


    def handle(peer_socket: socket.socket) -> None:             # This handles the sign up stage of the user.
        global primeNode                                        # When the sign up is complete it will send the info to
        global loadBalancer                                     # the login server
        global connections

        usernameOne = None
        usernameTwo = None
        pass1 = None
        pass2 = None

        try:
            received_data = peer_socket.recv(4096)
            print(received_data)
            while received_data:
                received_data = received_data.decode()

                if received_data == 'connectionsnow?':
                    connections = connections - 1
                    peer_socket.send(str(connections).encode("utf-8"))
                    loadBalancer = True
                    break

                elif received_data == 'back':
                    address = askforaddr(primeNode, 'ControlNode').split(':')
                    message = 'connect,' + address[0] + ',' + address[1] + ',' + address[2]
                    connections -= 1
                    peer_socket.send(message.encode("utf-8"))
                    break

                if len(received_data) < 8:
                    peer_socket.send(f"username and password must contain at least 8 charecters".encode("utf-8"))
                else:
                    if usernameOne is None:
                        usernameOne = received_data
                        peer_socket.send(f"Please Repeat the username: ".encode("utf-8"))
                    elif usernameTwo is None:
                        if received_data != usernameOne:
                            peer_socket.send(f"Usernames do not match {received_data}, {usernameOne}".encode("utf-8"))
                        else:
                            usernameTwo = received_data
                            peer_socket.send(f"Usernames Accepted. Please enter a password.".encode("utf-8"))
                    elif pass1 is None:
                        pass1 = received_data
                        peer_socket.send(f"Please Repeat the password: ".encode("utf-8"))
                    elif pass2 is None:
                        if received_data != pass1:
                            peer_socket.send(f"Usernames do not match".encode("utf-8"))
                        else:
                            pass2 = received_data
                            peer_socket.send(f"Sign Up Accepted. Redirecting...".encode("utf-8"))
                            time.sleep(2)
                            broadcastuser(primeNode, usernameOne, pass1)
                            address = askforaddr(primeNode, 'ControlNode')
                            address = address.split(':')
                            message = 'connect,' + address[0] + ',' + address[1] + ',' + address[2]
                            print(message)
                            connections -= 1
                            peer_socket.send(message.encode("utf-8"))

                received_data = peer_socket.recv(4096)
        except:
            connections -= 1
            print('User disconnected')


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
                peer_socket.send(f"What would you like your username to be? send 'back' if you want to return to the "
                                 f"last page".encode("utf-8"))

                connections += 1

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

    def askforaddr(prime, processtype):
        message = 'address:' + processtype
        return sendmessage(prime, message)


    def registerasfull(addr, host, port):
        message = 'max:SignUp:' + host + ':' + str(port)
        sendmessage(addr, message)

    def registerself(prime, host, port):
        message = 'service:' + 'SignUp:' + host + ':' + str(port)
        sendmessage(prime, message)

    def broadcastuser(prime, username, password):
        message = 'user:' + username + ':' + password
        sendmessage(prime, message)

    def sendmessage(addr, message):
        s = socket.socket()
        s.connect((addr['host'], addr['port']))
        s.sendall(message.encode())
        returnMessage = s.recv(1024).decode()
        return returnMessage


    print('Sign Up Service Started : ' + sys.argv[2] + ' - ' + sys.argv[1])
    threading.Thread(target=listen).start()
