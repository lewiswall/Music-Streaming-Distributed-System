import random
from uuid import uuid4


if __name__ == "__main__":
    import shlex
    import socket
    import sys
    import threading

    word_list = {"Waffle", "average"}
    rand_token = uuid4()


    def handle(peer_socket: socket.socket, parent) -> None:             #This handles the sign up stage of the user.
        usernameOne = None                                      #When the sign up is complete it will send the info to
        usernameTwo = None                                      #the login server
        pass1 = None
        pass2 = None
        print(parent)

        received_data = peer_socket.recv(4096)
        print(received_data)
        while received_data:
            received_data = received_data.decode()
            if(len(received_data) < 8):
                peer_socket.send(f"username and password must contain at least 8 charecters".encode("utf-8"))
                sendMessage(usernameOne, pass1)
            else:
                if(usernameOne is None):
                    usernameOne = received_data
                    peer_socket.send(f"Please Repeat the username: ".encode("utf-8"))
                elif(usernameTwo is None):
                    if(received_data != usernameOne):
                        peer_socket.send(f"Usernames do not match {received_data}, {usernameOne}".encode("utf-8"))
                    else:
                        usernameTwo = received_data
                        peer_socket.send(f"Usernames Accepted. Please enter a password.".encode("utf-8"))
                elif(pass1 is None):
                    pass1 = received_data
                    peer_socket.send(f"Please Repeat the password: ".encode("utf-8"))
                elif(pass2 is None):
                    if(received_data != pass1):
                        peer_socket.send(f"Usernames do not match".encode("utf-8"))
                    else:
                        pass2 = received_data
                        peer_socket.send(f"Sign Up Accepted.".encode("utf-8"))
                        sendMessage(usernameOne, pass1, parent)


            received_data = peer_socket.recv(4096)


    def sendMessage(username, password, parent):
        s = socket.socket()
        s.connect((parent['host'], parent['port']))
        message = 'user:' + username + ':' + password
        s.sendall(message.encode())
        message = s.recv(1024)
        message = message.decode()
        print(parent)

        if (message == 'ok'):
            print('Accepted User')
        else:
            print('User Not Accepted')
            print(message)



    def listen() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_port = int(sys.argv[1])
            parent = handleParent()

            # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(("127.0.0.1", server_port))
            server_socket.listen()

            while True:
                peer_socket, address = server_socket.accept()
                peer_socket.send(f'What would you like your username to be?'.encode("utf-8"))

                threading.Thread(target=handle, args=[peer_socket, parent]).start()

    def handleParent():
        parent = sys.argv[2].split(':')
        parentNode = {'type': parent[0],
                      'host': parent[1],
                      'port': int(parent[2])}
        return parentNode



    print('Sign up')
    print(sys.argv[2])
    print(rand_token)
    threading.Thread(target=listen).start()
