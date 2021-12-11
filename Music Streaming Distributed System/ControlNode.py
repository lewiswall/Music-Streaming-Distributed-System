
if __name__ == "__main__":
    import shlex
    import socket
    import sys
    import threading

    def handle(peer_socket: socket.socket, prime) -> None:

        print(prime)

        received_data = peer_socket.recv(4096)
        print(received_data)
        while received_data:


            received_data = peer_socket.recv(4096)



    def listen() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_port = int(sys.argv[1])
            server_host = sys.argv[2]
            prime = handlePrime()

            # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((server_host, server_port))
            server_socket.listen()

            while True:
                peer_socket, address = server_socket.accept()
                peer_socket.send(f'What would you like your username to be?'.encode("utf-8"))

                threading.Thread(target=handle, args=[peer_socket, prime]).start()

    def handlePrime():
        prime = sys.argv[3].split(':')
        primeNode = {'type': prime[0],
                      'host': prime[1],
                      'port': int(prime[2])}
        return primeNode





    print('ControlNode')
    print(sys.argv[2])
    threading.Thread(target=listen).start()
