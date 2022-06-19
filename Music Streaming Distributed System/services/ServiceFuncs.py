import socket

"""
This file contains functions which are reused by multiple services
"""

#Used by all other functions to send a message
def SendMessage(addr, message):
    s = socket.socket()
    s.connect((addr['host'], addr['port']))
    s.sendall(message.encode())
    returnMessage = s.recv(1024).decode()
    s.close()
    return returnMessage

def RegisterAsFull(primeAddr, serviceType, serviceHost, servicePort):
    message = 'max:' + serviceType + ':' + serviceHost + ':' + str(servicePort)
    SendMessage(primeAddr, message)


def RegisterWithPrime(primeAddr, serviceType, serviceHost, servicePort):
    message = 'service:' + serviceType + ':' + serviceHost + ':' + str(servicePort)
    return SendMessage(primeAddr, message)

def HandlePrime(prime):
    primeNode = {'type': prime[0],
                 'host': prime[1],
                 'port': int(prime[2])}
    return primeNode

def AskForAddr(primeAddr, serviceType):
    message = 'address:' + serviceType
    return SendMessage(primeAddr, message)