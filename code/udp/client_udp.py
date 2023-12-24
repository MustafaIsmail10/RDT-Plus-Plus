import socket


# setting up the scokcet
serverIP = "172.17.0.2"
serverPort = 8022
serverAddressPort = (serverIP, serverPort)
bufferSize = 4096


# # Create a UDP socket at client side
# sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)


# msgFromClient = "Send Files"

# bytesToSend = str.encode(msgFromClient)

# # Send to server using created UDP socket
# sock.sendto(bytesToSend, serverAddressPort)

# # Send starting message: "Send Files\n\n"
# # s.sendto(b"Send Files\n\n", serverAddressPort)
# # print("Sent starting message")

# while True:
#     msgFromServer = sock.recvfrom(bufferSize)

#     msgFromServer = msgFromServer[0].decode("utf-8")
#     print(msgFromServer)
#     if msgFromServer == "close":
#         print("We should stopped receiving files")
#         break

# data = s.recv(bufferSize)
# print(f"Received: {data!r}")


# msg = "Message from Server {}".format(msgFromServer[0])

# print(msg)


def main():
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.sendto(b"type:d\nseq:0\nlength:0\n\n", serverAddressPort)
    msg, address = sock.recvfrom(bufferSize)
    print(msg.decode("utf-8"))
    sock.close()


if __name__ == "__main__":
    main()
