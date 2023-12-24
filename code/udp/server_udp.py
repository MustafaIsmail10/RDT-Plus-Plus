import socket
import os

## Protocol:
## C -> "Send Files"
## S -> "num:<number of files>\n\n"
## Repeat
##  S -> "size: <file sieze>\n\n"
##  S -> file\n\n

## S -> "Close\n\n"
## C -> closes

# reading files from disk to memory
absolute_path = os.path.abspath("../")
object_path = "/root/objects"
files = []
for i in range(10):
    with open(f"{object_path}/large-{i}.obj", "rb") as f:
        files.append(f.read())
    with open(f"{object_path}/small-{i}.obj", "rb") as f:
        files.append(f.read())


localIP = "127.0.0.1"

localPort = 20001

bufferSize = 1024

localIP = "172.17.0.2"
localPort = 6500

serverAddressPort = (localIP, localPort)

msgFromServer = "Hello UDP Client"

bytesToSend = str.encode(msgFromServer)


clientIP = "172.17.0.3"
clientPort = 49104
clientAddressPort = (clientIP, clientPort)

# Create a datagram socket
s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Bind to address and ip
s.bind((localIP, localPort))

print("UDP server up and listening")

# Listen for incoming datagrams
while True:
    # # First receive "Send Files\n\n"
    # data = s.recv(bufferSize)
    # print(f"Received: {data!r}")
    # if data == b"Send Files\n\n":
    #     print("We should start sending files")
    #     s.sendto(f"num:{len(files)}\n\n".encode("utf-8"), serverAddressPort)

    bytesAddressPair = s.recvfrom(bufferSize)

    message = bytesAddressPair[0]

    address = bytesAddressPair[1]

    clientMsg = "Message from Client:{}".format(message)
    clientIP = "Client IP Address:{}".format(address)

    print(clientMsg)
    print(clientIP)

    # Sending a reply to client
    s.sendto(bytesToSend, address)


#
