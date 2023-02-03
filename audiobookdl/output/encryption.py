from Crypto.Cipher import AES
from audiobookdl.utils.audiobook import AudiobookFileEncryption, AESEncryption

def decrypt_file(path, encryption_method: AudiobookFileEncryption):
    if isinstance(encryption_method, AESEncryption):
        decrypt_file_aes(path, encryption_method.key, encryption_method.iv)

def decrypt_file_aes(path, key, iv):
    with open(path, "rb") as f:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(f.read())
    with open(path, "wb") as f:
        f.write(decrypted)
