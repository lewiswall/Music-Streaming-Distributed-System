
if (__name__ == "__main__"):
    import socket
    import struct
    import wave

    host = "127.0.0.1"
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen()
        print("Server started")

        with wave.open("sounds/example.wav", 'rb') as waveform:
            chunk_size = 4096

            client_socket, address = server_socket.accept()
            chunk_data = waveform.readframes(chunk_size)

            while chunk_data:
                client_socket.sendall(struct.pack("I", len(chunk_data)) + chunk_data)

                chunk_data = waveform.readframes(chunk_size)

            client_socket.close()
