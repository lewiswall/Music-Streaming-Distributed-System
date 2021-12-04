import struct

if __name__ == "__main__":
    import socket
    import sys
    import threading
    import wave

    root = "/Users/lewiswall/Desktop/pyaudio-example-main/sounds/"
    files = ['example', 'thunder', 'police', 'jaildoor']

    fileDetails = [{'name': 'example',
                   'channels': '2',
                   'rate': '11025',
                   'output': 'True',
                   'frames': '4096'
    }]

    def handle(peer_socket: socket.socket) -> None:

        received_data = peer_socket.recv(4096).decode()
        print(received_data)

        while received_data:
            if received_data in files:
                details = detailBuilder(received_data)

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
                peer_socket.send(f"'{received_data}' is not a correct command".encode(("utf-8")))


            received_data = peer_socket.recv(4096).decode()

    def listen() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_port = int(sys.argv[1])

            # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(("127.0.0.1", server_port))
            server_socket.listen()

            while True:
                peer_socket, address = server_socket.accept()
                peer_socket.send(b"Type 'list' to list the files available for streaming")

                threading.Thread(target=handle, args=[peer_socket]).start()

    def detailBuilder(file):
        for a in fileDetails:
            if file == a['name']:
                return 'play,' + a['channels'] + ',' + a['rate'] + ',' + a['output'] + ',' + a['frames']



    print("Service Node")
    threading.Thread(target=listen).start()