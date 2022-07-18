import ServiceFuncs
import time

if __name__ == "__main__":
    import socket
    import sys
    import threading

    primeNode = ""
    addrs = []
    loadBalancerType = sys.argv[4].split(':')[0]

    lowestCon = 50
    lowestConService = None

    # service = {'type' : type,
    #            'host' : host,
    #            'port' port,}

    def handle(peer_socket: socket.socket) -> None:
        global addrs
        global lowestConService
        global lowestCon

        lowestConService = addrs[0]
        try:
            recv_data = peer_socket.recv(4096).decode()
            if recv_data == 'client':
                if True:
                    lowestCon = 50
                    for a in addrs:
                        checkconnections(a)

                    if lowestCon >= 3:
                        startnewservice()
                        time.sleep(5)
                        for a in addrs:
                            checkconnections(a)

                    message = 'connect,' + lowestConService['type'] + ',' + lowestConService['host'] + ',' + \
                              lowestConService['port']
                    peer_socket.send(message.encode("utf-8"))
            elif recv_data.split(':')[0] == 'addr':
                service = recv_data.split('{')[1]
                service = '{' + service
                converted = eval(service)
                addrs.append(converted)
                peer_socket.send(b'ok')
        except:
            print('User unexpectedly disconnected')

    def listen() -> None:
        """
        Handles the incoming connection requests from peer services, delegating them to a handler thread.
        """

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            global primeNode
            global loadBalancerType

            server_port = int(sys.argv[1])
            server_host = sys.argv[2]
            primeNode = ServiceFuncs.HandlePrime(sys.argv[3].split(':'))
            print(primeNode)

            RegisterLoadWithPrime(primeNode, loadBalancerType, server_host, server_port)


            # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((server_host, server_port))
            server_socket.listen()

            while True:
                peer_socket, address = server_socket.accept()
                peer_socket.send(f'type??'.encode("utf-8"))

                threading.Thread(target=handle, args=[peer_socket]).start()


    def startnewservice():
        global primeNode
        message = 'newService:' + loadBalancerType + '.py'
        ServiceFuncs.SendMessage(primeNode, message)


    def checkconnections(addr):
        global lowestCon
        global lowestConService

        message = 'connectionsnow?'
        returnMessage = heartbeat(addr, message)      # will be the number of connections for each service
        returnMessage = int(returnMessage)
        if returnMessage < lowestCon:
            lowestCon = returnMessage
            lowestConService = addr


    #Has its own register with prime function because its handled differently to other services
    def RegisterLoadWithPrime(primeAddr, loadType, loadHost, loadPort):
        global addrs
        message = 'LoadBalancer:' + loadType + ':' + loadHost + ':' + str(loadPort)
        # return message will be the addresses of the services for the load balancer
        # returnMessage = sendmessage(prime, message)
        returnAddrs = ServiceFuncs.SendMessage(primeAddr, message)
        addrs = eval(returnAddrs)

    def heartbeat(addr, message):
        s = socket.socket()
        s.connect((addr['host'], int(addr['port'])))
        s.sendall(message.encode())
        # this is repeated because the services send a message meant for the client so
        # it allows the heartbeat to skip over it
        returnMessage = s.recv(1024).decode()
        returnMessage = s.recv(1024).decode()
        s.close()
        return returnMessage


    print(loadBalancerType + ' Load balancer ready : ' + str(sys.argv[2]) + ':' + sys.argv[1])
    threading.Thread(target=listen).start()
