import socket
import os
import json

SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 9050

SUPPORTED_MEDIA_TYPES = {'mp4', 'avi', 'mkv', 'mp3', 'wav'}


def MMP_header(json_size, operation_code, payload_size):
    return (
        json_size.to_bytes(2, 'big') +
        operation_code.to_bytes(1, 'big') +
        payload_size.to_bytes(5, 'big')
    )


while True:
    try:
        operation = int(input(
            "Enter the operation "
            "(1: compress, 2: change resolution, 3: change aspect ratio, 4: video to audio, 5: video to gif, 0: exit): "
        ))
    except ValueError:
        print("Please enter a valid number.")
        continue

    if operation == 0:
        print("Client closed.")
        break

    if operation not in [1, 2, 3, 4, 5]:
        print("Invalid operation. Please enter a number between 1 and 5.")
        continue

    filepath = input("Enter the media file path (with extension): ").strip()

    if not os.path.isfile(filepath):
        print("File does not exist.")
        continue

    filename = os.path.basename(filepath)
    media_type = filename.split('.')[-1].lower()

    if media_type not in SUPPORTED_MEDIA_TYPES:
        print("Unsupported media type. Supported types are: mp4, avi, mkv, mp3, wav.")
        continue

    json_data = {
        "filename": filename
    }

    json_bytes = json.dumps(json_data).encode('utf-8')
    json_size = len(json_bytes)
    payload_size = os.path.getsize(filepath)

    header = MMP_header(json_size, operation, payload_size)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.connect((SERVER_ADDRESS, SERVER_PORT))

            tcp_socket.sendall(header)
            tcp_socket.sendall(json_bytes)

            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    tcp_socket.sendall(chunk)
            print(f"File {filename} sent successfully.")

            response = tcp_socket.recv(8)
            output_size = int.from_bytes(response, 'big')

            print(f"Output file size: {output_size} bytes")

            with open(f'output_{filename}', 'wb') as f:
                received_bytes = 0
                while received_bytes < output_size:
                    chunk = tcp_socket.recv(4096)
                    if not chunk:
                        break
                    f.write(chunk)
                    received_bytes += len(chunk)

    except Exception as e:
        print(f"Connection or sending error: {e}")