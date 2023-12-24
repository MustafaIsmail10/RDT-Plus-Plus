"""
TCP Server that sends files to the client
"""
import socket
import os

HOST = "172.17.0.2"
PORT = 65432

# reading files from disk to memory
absolute_path = os.path.abspath('../')
object_path = "/root/objects"
large_files = []
small_files = []
for i in range(10):
    with open(f"{object_path}/large-{i}.obj", "rb") as f:
        large_files.append(f.read())
    with open(f"{object_path}/small-{i}.obj", "rb") as f:
        small_files.append(f.read())

files = large_files + small_files


def print_decoded(data):
    print(data.decode('utf-8'))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024)
            print(f"Received: {data!r}")
            if data == b"Send Files\n\n":
                conn.sendall(f"num:{len(files)}\n\n".encode("utf-8"))
                for file in files:
                    print(f"Sending file of size: {len(file)}")
                    conn.sendall(f"size:{len(file)}\n\n".encode("utf-8"))
                    print("Sending file...")
                    conn.sendall(file)
                print("Sending close")
                conn.sendall("Close\n\n".encode("utf-8"))
                conn.close()
                break

## Protocol:
## C -> "Send Files"
## S -> "num:<number of files>\n\n"
## Repeat
##  S -> "size: <file sieze>\n\n"
##  S -> file\n\n

## S -> "Close\n\n"
## C -> closes
