import socket

def SendMessage(host, port, message):
    s = socket.socket()
    s.connect((host, port))
    s.sendall(message.encode())
    returnMessage = s.recv(1024).decode()
    s.close()
    return returnMessage