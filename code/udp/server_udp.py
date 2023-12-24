import socket
import os
import threading


# setting up the scokcet
localIP = "172.17.0.2"
localPort = 8022
serverAddressPort = (localIP, localPort)
bufferSize = 4096

SEGMENT_SIZE = 2048
WINDOW_SIZE = 5
MAX_SEQUENCE_NUMBER = 65535


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


class RDTServer:
    def __init__(self, sock):
        self.sock = sock
        self.client_address = None

        self.send_buffer = []
        self.waiting_for_ack_buffer = {}
        self.window_size = WINDOW_SIZE
        self.next_sequence_number = MAX_SEQUENCE_NUMBER

        self.recv_buffer = []
        self.recv_buffer_lock = threading.Lock()
        self.recv_mutex = threading.Lock()
        self.recv_condition = threading.Condition(self.recv_mutex)

        self.send_buffer_lock = threading.Lock()
        self.waiting_for_ack_buffer_lock = threading.Lock()

        self.sending_mutex = threading.Lock()
        self.sending_condition = threading.Condition(self.sending_mutex)
        self.sending_thread = threading.Thread(target=self.sending_thread_func)

        self.receiving_thread = threading.Thread(target=self.receiving_thread_func)

        self.resending_mutex = threading.Lock()
        self.resending_condition = threading.Condition(self.resending_mutex)
        self.resending_thead = threading.Thread(target=self.resending_thead_func)

        self.sending_thread.start()
        self.receiving_thread.start()
        self.resending_thead.start()

    def send(self, msg):
        self.sock.sendto(msg.encode("utf-8"), self.client_address)

    def receive(self):
        data = self.sock.recv(bufferSize)
        return data.decode("utf-8")

    def sendto(self, msg, address):
        with self.sending_mutex:
            self.send_buffer_lock.acquire()
            self.client_address = address
            self.send_buffer.append(msg)
            self.send_buffer_lock.release()
            self.sending_condition.notify()

    def recv(self):
        with self.recv_mutex:
            self.recv_buffer_lock.acquire()
            while len(self.recv_buffer) == 0:
                self.recv_buffer_lock.release()
                print("waiting for message")
                self.recv_condition.wait()
                print("received message")

            self.recv_buffer_lock.acquire()
            message = self.recv_buffer.pop(0)
            self.recv_buffer_lock.release()
            return message

    def sending_thread_func(self):
        with self.sending_mutex:
            while True:
                if len(self.waiting_for_ack_buffer.keys()) <= self.window_size:
                    self.send_buffer_lock.acquire()
                    self.waiting_for_ack_buffer_lock.acquire()
                    if len(self.send_buffer) == 0:
                        self.send_buffer_lock.release()
                        self.waiting_for_ack_buffer_lock.release()
                        self.sending_condition.wait()
                        continue
                    message = self.send_buffer.pop(0)
                    self.waiting_for_ack_buffer[self.next_sequence_number] = message
                    self.next_sequence_number += 1
                    length = len(message)
                    segment = f"type:d\nseq:{self.next_sequence_number}\nlength:{length}\n\n{message}"
                    self.send(segment)
                    self.send_buffer_lock.release()
                    self.waiting_for_ack_buffer_lock.release()
                else:
                    self.sending_condition.wait()

    def message_parser(self, message):
        parts = message.split("\n\n")
        header = parts[0]
        header_parts = header.split("\n")
        type = header_parts[0].split(":")[1]
        seq = int(header_parts[1].split(":")[1])
        length = int(header_parts[2].split(":")[1])
        data = parts[1]
        return type, seq, length, data

    def ack_handler(self, seq):
        with self.sending_mutex:
            self.waiting_for_ack_buffer_lock.acquire()
            self.waiting_for_ack_buffer.pop(seq, None)
            self.waiting_for_ack_buffer_lock.release()
            self.sending_condition.notify()

    def receiving_thread_func(self):
        while True:
            message, client_address = self.sock.recvfrom(bufferSize)
            message = message.decode("utf-8")
            type, seq, length, data = self.message_parser(message)
            if type == "i":
                self.client_address = client_address
            elif type == "a":
                self.ack_handler(seq)
            elif type == "d":
                self.recv_buffer_lock.acquire()
                self.recv_buffer.append(data)
                self.recv_buffer_lock.release()
                print(f"Received segment {seq}")
                with self.recv_mutex:
                    self.recv_condition.notify()
                ack = f"type:a\nseq:{seq}\n\n"
                self.sendto(ack, client_address)

    def resending_thead_func(self):
        while True:
            # resend the segments that have not been acknowledged
            pass


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
    rdt_server = RDTServer(sock)
    while True:
        received_message = rdt_server.recv()
        print(received_message)


if __name__ == "__main__":
    main()
