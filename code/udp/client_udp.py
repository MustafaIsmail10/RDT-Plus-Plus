"""
This is the client code for the sending files application.

It uses RDTPlus class to send and receive files over the network.

Application Layer Protocol:
C -> "send"
S -> "num:<number of files>"
C -> "get"
Repeat for each file:
    S -> "size: <file sieze>\n\n"
    S -> file\n\n
C -> "ok"
S -> "close"
C -> closes
"""


import socket
from rdt_plus import RDTPlus
import ast
import hashlib

# setting up the scokcet
SERVER_IP = "172.17.0.2"
SERVER_PORT = 8032


def main():
    """
    This is the main function of the client.
    It creates a socket.
    It uses RDTPlus class to send and receive files over the network.

    It sends "send" to the server and waits for the number of files.
    It sends "get" to the server and waits for the files.
    It sends "ok" to the server and waits for the server to close.
    It closes the connection.
    """
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    serverAddressPort = (SERVER_IP, SERVER_PORT)
    client_rdt = RDTPlus(sock, False, serverAddressPort)
    client_rdt.send(["send".encode("utf-8")], serverAddressPort)
    msg, address = client_rdt.recv()
    msg = msg.decode("utf-8")
    num = int(msg.split(":")[1])
    client_rdt.send(["get".encode("utf-8")], serverAddressPort)
    for i in range(num):
        """
        This loop receives the files from the server.
        """
        msg, address = client_rdt.recv()
        msg = msg.decode("utf-8")
        headers, file = msg.split("\n\n")
        file = ast.literal_eval(file)
        size = int(headers.split("\n")[0].split(":")[1])
        checksum = headers.split("\n")[1].split(":")[1]
        hash_function = hashlib.md5()
        hash_function.update(file)
        computed_checksum = hash_function.hexdigest()
        if computed_checksum != checksum:
            print("files checksums are not equal")
        else:
            print("file with size:{size} is received".format(size=size))

    print("All files received")
    client_rdt.send(["ok".encode("utf-8")], serverAddressPort)

    msg, address = client_rdt.recv()
    msg = msg.decode("utf-8")
    if msg == "close":
        client_rdt.close()


if __name__ == "__main__":
    main()
