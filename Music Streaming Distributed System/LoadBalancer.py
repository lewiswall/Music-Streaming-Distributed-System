import random

if __name__ == "__main__":
    import shlex
    import socket
    import sys
    import threading

    processors = []

    def handle(peer_socket: socket.socket) -> None:
        """
        Handles an individual connection request that has already been received and needs monitoring for new data.
        :param peer_socket: Individual peer connection.
        """



        received_data = peer_socket.recv(4096)

        while received_data:
            peer_socket.send(received_data)

            received_data = peer_socket.recv(4096)

    def listen() -> None:
        """
        Handles the incoming connection requests from peer services, delegating them to a handler thread.
        """

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

                threading.Thread(target=handle, args=[peer_socket]).start()

    def sortAddressess(addresses):
        print(addresses)

    def handlePrime():
        parent = sys.argv[3].split(':')
        parentNode = {'type': parent[0],
                      'host': parent[1],
                      'port': int(parent[2])}
        return parentNode


    threading.Thread(target=listen).start()


    print('Load balancer ready')
    sortAddressess(sys.argv[2])