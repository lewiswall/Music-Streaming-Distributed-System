from uuid import uuid4
import time
import ServiceFuncs

if __name__ == "__main__":
    import socket
    import sys
    import threading

    logins = []
    connections = 0
    primeNode = ""
    loadBalancer = False

    def handle(peer_socket: socket.socket) -> None:
        global logins
        global connections
        global loadBalancer

        user1 = None
        actualPass = None
        enteredPass = None

        try:
            received_data = peer_socket.recv(4096)

            while received_data:
                received_data = received_data.decode()
                if received_data == 'connectionsnow?':
                    connections = connections - 1
                    peer_socket.send(str(connections).encode("utf-8"))
                    loadBalancer = True
                    break
                elif received_data == '#info#':
                    connections = connections - 1
                    peer_socket.send(str(logins).encode("utf-8"))
                    break

                elif received_data == 'back':
                    address = ServiceFuncs.AskForAddr(primeNode, 'ControlNode').split(':')
                    message = 'connect,' + address[0] + ',' + address[1] + ',' + address[2]
                    connections -= 1
                    peer_socket.send(message.encode("utf-8"))
                    break
                elif received_data.split(':')[0] == 'user':
                    login = received_data.split(':')
                    addlogin(login[1], login[2])
                    connections = connections - 1
                    peer_socket.send('ok'.encode("utf-8"))
                    break

                elif received_data.split(':')[0] == 'usertoken':
                    connections -= 1
                    received_data = received_data.split(':')
                    for login in logins:
                        if login['user'] == received_data[1]:
                            login['token'] = received_data[2]
                    break
                else:
                    if user1 is None:
                        userCorrect = False
                        for a in logins:
                            if received_data == a['user']:
                                userCorrect = True
                                user1 = a['user']
                                actualPass = a['pass']
                                peer_socket.send(f"Enter your password:".encode("utf-8"))
                        if not userCorrect:
                            peer_socket.send("You have entered the Incorrect Username".encode("utf-8"))
                    elif enteredPass is None:
                        if received_data == actualPass:
                            rand_token = uuid4()
                            addtoken(user1, rand_token)
                            message = 'token:' + str(rand_token) + ':' + user1
                            peer_socket.send(message.encode("utf-8"))
                            time.sleep(0.5)

                            broadcastusertoken(primeNode, user1, rand_token)
                            print("login success")
                            peer_socket.send(f"Login Successful. Redirecting...".encode("utf-8"))
                            time.sleep(1)

                            address = ServiceFuncs.AskForAddr(primeNode, 'ControlNode').split(':')
                            message = 'connect,' + address[0] + ',' + address[1] + ',' + address[2]
                            connections -= 1
                            peer_socket.send(message.encode("utf-8"))

                        else:
                            peer_socket.send(f"You have entered the wrong password".encode("utf-8"))
                            print("password wrong")

                received_data = peer_socket.recv(4096)
        except:
            connections -= 1
            print('User Disconnected')

    def listen() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            global primeNode
            global loadBalancer
            global connections

            server_port = int(sys.argv[1])
            server_host = sys.argv[2]
            primeNode = ServiceFuncs.HandlePrime(sys.argv[3].split(':'))
            requestinfo()
            ServiceFuncs.RegisterWithPrime(primeNode, 'Login', server_host, server_port)

            # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((server_host, server_port))
            server_socket.listen()

            while True:
                peer_socket, address = server_socket.accept()
                peer_socket.send(f'What is your username? Type "back" to return to the last page '.encode("utf-8"))
                connections += 1

                if connections == 3:
                    if not loadBalancer:
                        ServiceFuncs.RegisterAsFull(primeNode, 'Login', server_host, server_port)
                        loadBalancer = True

                threading.Thread(target=handle, args=[peer_socket]).start()

    def addtoken(user, token):
        global logins
        for log in logins:
            if log['user'] == user:
                log['token'] = token


    def addlogin(user, password):
        global logins
        newLogin = {'user': user,
                    'pass': password,
                    'token': None}
        logins.append(newLogin)

    def requestinfo():
        global logins
        message = 'addrs:Login'
        addresses = ServiceFuncs.SendMessage(primeNode, message)           # returns another login address from prime node
        addresses = eval(addresses)

        if addresses:
            address = addresses[0]
            message = '#info#'
            s = socket.socket()
            s.connect((address['host'], int(address['port'])))
            s.sendall(message.encode())
            returnMessage = s.recv(1024).decode()
            returnMessage = s.recv(1024).decode()
            logins = eval(returnMessage)


    def broadcastusertoken(prime, user, token):
        message = 'usertoken:' + user + ':' + str(token)
        ServiceFuncs.SendMessage(prime, message)


    print("Login : " + str(sys.argv[2]) + ':' + sys.argv[1])
    threading.Thread(target=listen).start()
