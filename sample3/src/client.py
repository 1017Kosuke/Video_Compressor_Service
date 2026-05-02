import socket
from rsa import generate_keys, encrypt_message, decrypt_message 
import os


def header(operation, json_size):
    return operation.to_bytes(1, 'big') + json_size.to_bytes(7, 'big')


tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = "127.0.0.1"
server_port = 9000

tcp_socket.connect((server_address, server_port))



try:
    private_key,public_key = generate_keys()

    print(f"Public Key: {public_key}")
    print(f"Private Key: {private_key}")

    tcp_socket.send(public_key)

    filepath = input("Enter the media file path (with extension): ").strip()

    if not os.path.isfile(filepath):
        print("File does not exist.")
        pass

    filename = os.path.basename(filepath).encode()
    media_type = filename.split('.')[-1].lower()
    operation = input(" -- Choose an option -- \n1: compress video \n2: convert file type \n").encode()
    
    if(operation == b"1"):
        file_size = filename.__sizeof__()
        media_type = filename.split(b".")[-1]
        json_data = {
            "file_size": file_size,
            "media_type": media_type
        }
    elif(operation == b"2"):
        file_size = filename.__sizeof__()
        media_type = filename.split(b".")[-1].lower()
        type_to_convert = input("Enter the type to convert to: ").encode()

        json_data = {
            "file_size": file_size,
            "media_type": media_type,
            "type_to_convert": type_to_convert.decode()
        }

    json_data = str(json_data).encode()
    json_size = json_data.__sizeof__()
    tcp_socket.send(header(int(operation), json_size))
    tcp_socket.send(str(json_data).encode())

    with open("./sample3/src/" + filename, "rb") as f:
        while True:
            chunk = f.read(2048)
            if not chunk:
                break
            encrypted_chunk = encrypt_message(public_key, chunk)
            tcp_socket.sendall(encrypted_chunk)
        
    response = tcp_socket.recv(8)
    output_size = int.from_bytes(response, 'big')
    print(f"Output size: {output_size} bytes")

    with open(f"output_{filename.decode()}", "wb") as f:
        received_bytes = 0
        while received_bytes < output_size:
            chunk = tcp_socket.recv(2048)
            if not chunk:
                break
            decrypted_chunk = decrypt_message(private_key, chunk)
            f.write(decrypted_chunk)
            received_bytes += len(decrypted_chunk)
finally:
    tcp_socket.close()



