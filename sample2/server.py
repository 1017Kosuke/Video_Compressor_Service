import socket
import os
import subprocess
import json

SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 9050
DPATH = './sample2/temp'

OPERATION = {
    1: 'compress',
    2: 'change_resolution',
    3: 'change_aspect_ratio',
    4: 'video_to_audio',
    5: 'video_to_gif'
}

try:
    os.makedirs(DPATH, exist_ok=True)
except Exception as e:
    print(f"Failed to create directory {DPATH}: {e}")
    exit(1)


def recv_exact(conn, size):
    """指定サイズぶん必ず受け取る"""
    data = b''
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Connection closed before receiving enough data.")
        data += chunk
    return data


def build_output_and_command(operation_code, input_path):
    """操作番号に応じて ffmpeg コマンドと出力パスを返す"""
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)

    if operation_code == 1:
        output_path = os.path.join(DPATH, f'compressed_{filename}')
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vcodec', 'libx264',
            '-crf', '28',
            output_path
        ]

    elif operation_code == 2:
        output_path = os.path.join(DPATH, f'resized_{filename}')
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', 'scale=1280:720',
            output_path
        ]

    elif operation_code == 3:
        output_path = os.path.join(DPATH, f'aspect_ratio_changed_{filename}')
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', 'setdar=16:9',
            output_path
        ]

    elif operation_code == 4:
        output_path = os.path.join(DPATH, f'audio_{name}.mp3')
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-q:a', '0',
            '-map', 'a',
            output_path
        ]

    elif operation_code == 5:
        output_path = os.path.join(DPATH, f'gif_{name}.gif')
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', 'fps=10,scale=320:-1:flags=lanczos',
            output_path
        ]

    else:
        raise ValueError("Invalid operation code.")

    return output_path, cmd


server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((SERVER_ADDRESS, SERVER_PORT))
server_sock.listen(1)

print(f'Server is listening on {SERVER_ADDRESS}:{SERVER_PORT}')

while True:
    conn, client_address = server_sock.accept()
    print(f'Connection from {client_address[0]}:{client_address[1]}')

    with conn:
        try:
            # header は 8 bytes 固定
            header_data = recv_exact(conn, 8)

            json_size = int.from_bytes(header_data[0:2], byteorder='big')
            operation_code = int.from_bytes(header_data[2:3], byteorder='big')
            payload_size = int.from_bytes(header_data[3:8], byteorder='big')

            print(f'Received header: json_size={json_size}, operation_code={operation_code}, payload_size={payload_size}')

            json_bytes = recv_exact(conn, json_size)
            request_info = json.loads(json_bytes.decode('utf-8'))

            filename = os.path.basename(request_info['filename'])
            print(f'Received filename: {filename}')
            print(f'Operation: {OPERATION.get(operation_code, "unknown")}')

            file_bytes = recv_exact(conn, payload_size)

            input_path = os.path.join(DPATH, filename)
            with open(input_path, 'wb') as f:
                f.write(file_bytes)

            print(f'Media file {filename} received and saved successfully.')

            output_path, cmd = build_output_and_command(operation_code, input_path)
            subprocess.run(cmd, check=True)

            print(f'Processing completed: {os.path.basename(output_path)}')

            # 元ファイル削除
            os.remove(input_path)
            print(f'Temporary file {filename} removed.')

            output_size = os.path.getsize(output_path)

            conn.sendall(output_size.to_bytes(8, 'big'))

            with open(output_path, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    conn.sendall(chunk)

            print(f'Output file {os.path.basename(output_path)} sent to client.')
            os.remove(output_path)
            print(f'Temporary output file {os.path.basename(output_path)} removed.')

        except Exception as e:
            print(f'Error while handling client {client_address}: {e}')
            try:
                conn.sendall(f'Error: {e}'.encode('utf-8'))
            except:
                pass