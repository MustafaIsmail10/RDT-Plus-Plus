import socket
from rdt_plus import RDTPlus
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
    client_rdt = RDTPlus(sock, False, serverAddressPort)
    client_rdt.send(["send".encode("utf-8")], serverAddressPort)
    msg, address = client_rdt.recv()
    msg = msg.decode("utf-8")
    num = int(msg.split(":")[1])
    client_rdt.send(["get".encode("utf-8")], serverAddressPort)
    for i in range(num):
        msg, address = client_rdt.recv()
        msg = msg.decode("utf-8")
        headers, file = msg.split("\n\n")
        file = ast.literal_eval(file)
        size = int(headers.split("\n")[0].split(":")[1])
        checksum = headers.split("\n")[1].split(":")[1]
        print("file with size:{size} is received".format(size=size))

    print("All files received")
    client_rdt.send(["ok".encode("utf-8")], serverAddressPort)

    msg, address = client_rdt.recv()
    msg = msg.decode("utf-8")
    if msg == "close":
        client_rdt.close()

    # x = client_rdt.recv()
    # if ast.literal_eval(x[0]).decode("utf-8") == "close":
    #     client_rdt.close()
    # print(conntection_status)

    # client_rdt.sendto("Send Files\n\n".encode("utf-8"), serverAddressPort)
    # msg = client_rdt.recv()
    # print(ast.literal_eval(msg[0]).decode("utf-8"))


if __name__ == "__main__":
    main()
