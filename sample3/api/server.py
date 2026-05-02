import socket
import os
import subprocess

tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = "127.0.0.1"
server_port = 9000
DPATH = "./sample3/api/temp"

try:
    os.mkdir(DPATH)
except FileExistsError:
    pass

def build_output_and_command(operation_code, input_path):
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
        output_path = os.path.join(DPATH, f'converted_{name}.mp4')
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            output_path
        ]
    else:
        raise ValueError("Invalid operation code.")

    return output_path,cmd

tcp_socket.bind((server_address, server_port))
tcp_socket.listen(1)

while True:
    conn, client_address = tcp_socket.accept()
    print(f"Connection from {client_address[0]}:{client_address[1]}")
    
    with conn:
        try:
            public_key = conn.recv(2048)
            print(f"Received Public Key: {public_key}")

            with open(DPATH + "/public_key.pem", "wb") as f:
                f.write(public_key)

            header = conn.recv(8)
            operation = int.from_bytes(header[:1], 'big')
            json_size = int.from_bytes(header[1:], 'big')

            json_data = conn.recv(json_size)
            print(f"Received JSON Data: {json_data}")

            output_path, cmd = build_output_and_command(operation, json_data)
            subprocess.run(cmd, check=True)

            print(f"Operation completed. Output saved to {output_path}")

            output_size = os.path.getsize(output_path)

            conn.sendall(output_size.to_bytes(8, 'big'))

            with open(output_path, "rb") as f:
                while True:
                    chunk = f.read(2048)
                    if not chunk:
                        break
                    conn.sendall(chunk)
            
            print(f"Output file {os.path.basename(output_path)} sent to client.")
            os.remove(output_path)
            print(f"Temporary output file {os.path.basename(output_path)} removed.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()