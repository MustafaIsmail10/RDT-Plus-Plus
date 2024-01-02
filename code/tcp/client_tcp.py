# echo-client.py

import socket

HOST = "172.17.0.2"
PORT = 65432

# Decode the number from the binary string
def decode_num(binary_string):
    # binary_string = b'num:20'
    decoded_string = binary_string.decode('utf-8')
    number_string = decoded_string.split(':')[1]
    number = int(number_string)
    return number

# Receive byte stream until a suffix is encountered
def recv_until(s, suffix):
    message = b''
    while not message.endswith(suffix):
        chunk = s.recv(1)
        if not chunk:
            raise IOError('Socket closed')
        message += chunk
    return message

def main():
    received_files = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(b"Send Files\n\n")
        data = recv_until(s, b"\n\n")
        num = decode_num(data)
        print(f"Received num: {num}")
        
        # For number of files to receive
        for n in range(num):
            size_data = recv_until(s, b"\n\n")
            size = decode_num(size_data)
            print(f"Received size: {size}")
            file_data = s.recv(size)
            received_files.append(file_data)
            print(f"Received file")

        data = recv_until(s, b"\n\n")
        print(f"Received: {data!r}")
        if data == b"Close\n\n":
            s.close()

    print(f"Received {len(received_files)} files")

if __name__ == "__main__":
    main()