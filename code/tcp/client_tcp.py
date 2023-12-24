# echo-client.py

import socket

HOST = "172.17.0.2"
PORT = 65432

def decode_num(binary_string):
    # binary_string = b'num:20'
    decoded_string = binary_string.decode('utf-8')
    number_string = decoded_string.split(':')[1]
    number = int(number_string)
    return number

def recv_until(s, suffix):
    message = b''
    while not message.endswith(suffix):
        chunk = s.recv(1)
        if not chunk:
            raise IOError('Socket closed')
        message += chunk
    return message

received_files = []
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Send Files\n\n")
    while True:
        # num:20
        data = recv_until(s, b"\n\n")
        # print(f"Received: {data!r}")
        # decoded = data.decode('utf-8')
        # print(decoded)
        num = decode_num(data)
        print(f"Received num: {num}")
        # loop : size + file
        for n in range(num):
            # data = s.recv(1024)
            size_data = recv_until(s, b"\n\n")
            # print(f"Received: {size_data!r}")
            size = decode_num(size_data)
            print(f"Received size: {size}")
            file_data = s.recv(size)
            received_files.append(file_data)
            print(f"Received file")
        data = recv_until(s, b"\n\n")
        print(f"Received: {data!r}")
        if data == b"Close\n\n":
            s.close()
        break

print(f"Received {len(received_files)} files")