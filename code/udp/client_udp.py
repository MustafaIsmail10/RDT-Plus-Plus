import socket


msgFromClient = "Hello UDP Server"

bytesToSend = str.encode(msgFromClient)

# serverAddressPort   = ("127.0.0.1", 20001)

localIP = "172.17.0.2"
localPort = 6500
serverAddressPort = (localIP, localPort)
bufferSize = 4096


# Create a UDP socket at client side
s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Send to server using created UDP socket
s.sendto(bytesToSend, serverAddressPort)

# Send starting message: "Send Files\n\n"
# s.sendto(b"Send Files\n\n", serverAddressPort)
# print("Sent starting message")

msgFromServer = s.recvfrom(bufferSize)
# data = s.recv(bufferSize)
# print(f"Received: {data!r}")


msg = "Message from Server {}".format(msgFromServer[0])

print(msg)
