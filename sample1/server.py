import sys
import socket
import os

tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = "127.0.0.1"
server_port = 9050
dpath = "./sample1/temp"




try:
    os.makedirs(dpath, exist_ok=True)
except Exception as e:
    sys.stderr.write("Failed to create directory {}: {}\n".format(dpath, e))
    sys.stderr.flush()
    sys.exit(1)

try:
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind((server_address, server_port))
    tcp_socket.listen(5)
    sys.stdout.write("Server is listening on {}:{}\n".format(server_address, server_port))
    sys.stdout.flush()
except Exception as e:
    sys.stderr.write("Failed to start server: {}\n".format(e))
    sys.stderr.flush()
    sys.exit(1)


def recv_exact(conn, n):
    """nバイトちょうど受信する"""
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data


while True:
    conn, client_address = tcp_socket.accept()
    try:
        sys.stdout.write("Connection from {}:{}\n".format(client_address[0], client_address[1]))
        sys.stdout.flush()

        header = recv_exact(conn, 12)
        if not header:
            continue

        filename_size = int.from_bytes(header[:4], byteorder="big")
        file_size = int.from_bytes(header[4:12], byteorder="big")

        filename_bytes = recv_exact(conn, filename_size)
        if not filename_bytes:
            continue

        filename = filename_bytes.decode("utf-8")
        save_path = os.path.join(dpath, filename)

        remaining = file_size
        with open(save_path, "ab") as f:
            while remaining > 0:
                chunk = conn.recv(min(4096, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
                print("received {} bytes, remaining {}".format(len(chunk), remaining))

        if remaining == 0:
            sys.stdout.write(
                "Received file '{}' ({} bytes) from {}:{}\n".format(
                    filename, file_size, client_address[0], client_address[1]
                )
            )
            sys.stdout.flush()
            conn.sendall("OK: file received".encode("utf-8"))
        else:
            conn.sendall("ERROR: incomplete file transfer".encode("utf-8"))

    except Exception as e:
        sys.stderr.write("Error handling client {}: {}\n".format(client_address, e))
        sys.stderr.flush()
    finally:
        conn.close()