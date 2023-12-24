import socket
import os
from rdt import RDT


# setting up the scokcet
localIP = "172.17.0.2"
localPort = 8032
serverAddressPort = (localIP, localPort)

SEGMENT_SIZE = 2048


## Application Layer Protocol:
## C -> "Send Files"
## S -> "num:<number of files>\n\n"
## Repeat
##  S -> "size: <file sieze>\n\n"
##  S -> file\n\n
## S -> "close\n\n"
## C -> closes


# reading files from disk to memory
absolute_path = os.path.abspath("../")
object_path = "/root/objects"
files = []
checksums = []
for i in range(1):
    with open(f"{object_path}/large-{i}.obj", "rb") as f:
        files.append(f.read())
    with open(f"{object_path}/large-{i}.obj.md5", "r") as f:
        checksums.append(f.read())
    with open(f"{object_path}/small-{i}.obj", "rb") as f:
        files.append(f.read())
    with open(f"{object_path}/small-{i}.obj.md5", "r") as f:
        checksums.append(f.read())


def construct_objects_dic_and_ids():
    objects_dic = {}
    objects_ids = []
    for file_id in range(len(files)):
        file = files[file_id]
        file_segments = []
        for i in range(0, len(file), SEGMENT_SIZE):
            file_segments.append(file[i : i + SEGMENT_SIZE])

        objects_dic[file_id] = (
            file_segments,
            checksums[file_id],
            len(file_segments),
            0,
        )
        objects_ids.append(file_id)

    return objects_dic, objects_ids


# # Listen for incoming datagrams
# while True:
#     msgFromServer = "Hello UDP Server"
#     bytesToSend = str.encode(msgFromServer)
#     # # First receive "Send Files\n\n"
#     # data = s.recv(bufferSize)
#     # print(f"Received: {data!r}")
#     # if data == b"Send Files\n\n":
#     #     print("We should start sending files")
#     #     s.sendto(f"num:{len(files)}\n\n".encode("utf-8"), serverAddressPort)

#     client_message, client_address = sock.recvfrom(bufferSize)
#     client_message = client_message.decode("utf-8")

#     print("Connection from: " + str(client_address))

#     if client_message == "Send Files":
#         objects_dic, objects_ids = construct_objects_dic_and_ids()

#         print("Files Transfer Requested")
#         sock.sendto(f"num:{len(files)}\n\n".encode("utf-8"), client_address)
#         for id in objects_ids:
#             file_segments, checksum, num_segments, segment_id = objects_dic[id]
#             for segment_id in range(num_segments):
#                 sock.sendto(
#                     f"size:{len(file_segments[segment_id])}\n\n".encode("utf-8"),
#                     client_address,
#                 )
#                 sock.sendto(file_segments[segment_id], client_address)
#                 print(f"Sent segment {segment_id} of file {id}")

#         sock.sendto("close".encode("utf-8"), client_address)
#     clientMsg = "Message from Client:{}".format(client_message)
#     clientIP = "Client IP Address:{}".format(client_address)

#     print(clientMsg)
#     print(clientIP)

#     # Sending a reply to client
#     sock.sendto(bytesToSend, client_address)


def main():
    # Create a datagram socket
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    # Bind to address and ip
    sock.bind(serverAddressPort)
    print(f"RDT server up and listening on port {localPort}")
    rdt_server = RDT(sock, True)
    while True:
        received_message = rdt_server.recv()
        print(received_message)
        rdt_server.sendto(received_message[0], received_message[1])


if __name__ == "__main__":
    main()
