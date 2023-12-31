"""
This is the server code for the sending files application.

It uses RDTPlus class to send and receive files over the network.

Application Layer Protocol:
C -> "send"
S -> "num:<number of files>"
C -> "get"
Repeat for each file:
    S -> "size: <file sieze>\n\n"
    S -> file\n\n
C -> "ok"
C -> "close"
S -> closes
"""

import socket
import os
from rdt_plus import RDTPlus
import hashlib

# setting up the scokcet
localIP = "172.17.0.2"
localPort = 8032
serverAddressPort = (localIP, localPort)

SEGMENT_SIZE = 2048


# reading files from disk to memory
absolute_path = os.path.abspath("../")
object_path = "/root/objects"
files = []
checksums = []
for i in range(10):
    with open(f"{object_path}/large-{i}.obj", "rb") as f:
        data = f.read()
        hash_md5 = hashlib.md5()
        hash_md5.update(data)
        hash_value = hash_md5.hexdigest()
        print(f"hash value of file {i} is {hash_value}")
        files.append(data)

    with open(f"{object_path}/large-{i}.obj.md5", "r") as f:
        data = f.read()
        print("The read checksum is: ", data)
        checksums.append(data)
    with open(f"{object_path}/small-{i}.obj", "rb") as f:
        files.append(f.read())
    with open(f"{object_path}/small-{i}.obj.md5", "r") as f:
        checksums.append(f.read())


def main():
    """
    This is the main function of the server.
    It creates a socket, binds it to the server address and port and listens for incoming messages.
    It uses RDTPlus class to send and receive files over the network.
    """
    # Create a datagram socket
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    # Bind to address and ip
    sock.bind(serverAddressPort)
    print(f"RDT server up and listening on port {localPort}")
    rdt_plus_server = RDTPlus(sock, True)

    while True:
        """
        This loop listens for incoming messages.
        It receives a message and address.
        It decodes the message and checks if it is "send" or "get".
        If it is "send", it sends the number of files to the client.
        If it is "get", it sends the files to the client.
        if it is "ok", it closes the connection.
        """
        received_message, address = rdt_plus_server.recv()
        received_message = received_message.decode("utf-8")
        if received_message == "send":
            rdt_plus_server.send([f"num:{len(files)}".encode("utf-8")], address)
        elif received_message == "get":
            msgs = []
            for file_id in range(len(files)):
                msg = (
                    f"size:{len(files[file_id])}\nchecksum:{checksums[file_id]}\n\n"
                    + str(files[file_id])
                )
                msg = msg.encode("utf-8")
                msgs.append(msg)

            rdt_plus_server.send(msgs, address)
        elif received_message == "ok":
            print("All files sent")
            rdt_plus_server.send(["close".encode("utf-8")], address)

            rdt_plus_server.cleanup_server()


if __name__ == "__main__":
    main()
