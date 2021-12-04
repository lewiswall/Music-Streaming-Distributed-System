import random
from uuid import uuid4

if __name__ == "__main__":
    import shlex
    import socket
    import sys
    import threading

    lewis = {'user': 'lewiswall',
              'pass': 'lewiswall'}

    logins = [lewis]
    rand_token = uuid4()



    def handle(peer_socket: socket.socket) -> None:
        user1 = None
        password = None
        password1 = None

        received_data = peer_socket.recv(4096)
        print(received_data)

        while received_data:
            received_data = received_data.decode()
            if(received_data.split(':')[0] == 'user'):
                login = received_data.split(':')
                addLogin(login[1], login[2])
                print(logins)
            else:
                if(user1 is None):
                    for a in logins:
                        if received_data == a['user']:
                            user1 = a['user']
                            password = a['pass']
                            print("username successfull")
                            print(user1)
                            peer_socket.send(f"Enter your password:".encode("utf-8"))
                elif(password1 is None):
                    if received_data == password:
                        print("login sucess")
                        peer_socket.send(f"Login Successful".encode("utf-8"))
                    else:
                        peer_socket.send(f"You have entered the wrong password".encode("utf-8"))
                        print("pass wrong")


            received_data = peer_socket.recv(4096)

    def listen() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_port = int(sys.argv[1])

            # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(("127.0.0.1", server_port))
            server_socket.listen()

            while True:
                peer_socket, address = server_socket.accept()
                peer_socket.send(f'What is your username?'.encode("utf-8"))

                threading.Thread(target=handle, args=[peer_socket]).start()

    def addLogin(user, password):
        newLogin = {'user': user,
                    'pass': password}
        logins.append(newLogin)

    print("Login")
    print(rand_token)
    threading.Thread(target=listen).start()