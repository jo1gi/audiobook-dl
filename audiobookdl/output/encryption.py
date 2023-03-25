from Crypto.Cipher import AES
from audiobookdl.utils.audiobook import AudiobookFileEncryption, AESEncryption

def decrypt_file(path: str, encryption_method: AudiobookFileEncryption):
    """Decrypt encrypted file in place"""
    if isinstance(encryption_method, AESEncryption):
        decrypt_file_aes(path, encryption_method.key, encryption_method.iv)

def decrypt_file_aes(path: str, key: bytes, iv: bytes):
    """Decrypt AES encrypted file in place"""
    with open(path, "rb") as f:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(f.read())
    with open(path, "wb") as f:
        f.write(decrypted)
