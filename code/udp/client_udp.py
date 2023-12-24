import socket
from rdt import RDT
import ast

# setting up the scokcet
SERVER_IP = "172.17.0.2"
SERVER_PORT = 8032


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
    serverAddressPort = (SERVER_IP, SERVER_PORT)
    client_rdt = RDT(sock, False, serverAddressPort)
    client_rdt.sendto("Send Files\n\n".encode("utf-8"), serverAddressPort)
    msg = client_rdt.recv()
    print(ast.literal_eval(msg[0]).decode("utf-8"))


if __name__ == "__main__":
    main()
