import socket
import sys
import os

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = "127.0.0.1"
server_port = 9050

try:
    sock.connect((server_address, server_port))
except socket.error as err:
    print(err)
    sys.exit(1)


def protocol_header(filename_size, file_size):
    return filename_size.to_bytes(4, byteorder="big") + file_size.to_bytes(8, byteorder="big")


while True:
    filename_input = input("Enter filename to send (or 'exit' to quit): ")

    if filename_input.lower() == "exit":
        print("Exiting client.")
        break

    filepath = filename_input if filename_input.endswith(".mp4") else filename_input + ".mp4"

    if not os.path.exists(filepath):
        print("File does not exist:", filepath)
        continue

    with open(filepath, "rb") as f:
        f.seek(0, os.SEEK_END)
        filesize = f.tell()
        f.seek(0)

        filename = os.path.basename(f.name)
        filename_bytes = filename.encode("utf-8")

        header = protocol_header(len(filename_bytes), filesize)

        sock.sendall(header)
        sock.sendall(filename_bytes)

        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            print("Sending...")
            sock.sendall(chunk)

    data = sock.recv(1024)
    if not data:
        break

    print("Server response: {}".format(data.decode("utf-8")))

sock.close()