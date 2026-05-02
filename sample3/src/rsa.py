from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import binascii

# 鍵ペアを生成
def generate_keys():
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key

# 公開鍵でメッセージを暗号化
def encrypt_message(public_key, message):
    key = RSA.import_key(public_key)
    cipher = PKCS1_OAEP.new(key)
    encrypted_message = cipher.encrypt(message.encode())
    return binascii.hexlify(encrypted_message).decode()

# 秘密鍵でメッセージを復号化
def decrypt_message(private_key, encrypted_message):
    key = RSA.import_key(private_key)
    cipher = PKCS1_OAEP.new(key)
    decrypted_message = cipher.decrypt(binascii.unhexlify(encrypted_message))
    return decrypted_message.decode()

# メイン処理
# 鍵ペアの生成
private_key, public_key = generate_keys()

# メッセージの暗号化
message = "Hello, RSA!"
encrypted = encrypt_message(public_key, message)
print(f"暗号化されたメッセージ: {encrypted}")

# メッセージの復号化
decrypted = decrypt_message(private_key, encrypted)
print(f"復号化されたメッセージ: {decrypted}")
