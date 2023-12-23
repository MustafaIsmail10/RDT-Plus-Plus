"""
TCP Server that sends files to the client
"""

import socket
import pickle

HOST = "172.17.0.2"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)


# reading files from disk to memory
# large_files = []
# small_files = []
# for i in range(10):
#     with open(f"large_file_{i}.obj", "rb") as f:
#         large_files.append(f.read())
#     with open(f"small_file_{i}.obj", "rb") as f:
#         small_files.append(f.read())


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            # Send Files

            data = conn.recv(1024)
            if not data:
                break
            conn.sendall("Fuck you, Do not make tcp request again.".encode("utf-8"))
            conn.close()


## C -> "Send Files"
## S -> "num:<number of files> \n\n"
## Repeat
##  S -> "size: <file sieze> \n\n"
##  S -> file \n\n

## S -> "Close\n\n"
## C -> closes
