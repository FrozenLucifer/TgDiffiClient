import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from base64 import urlsafe_b64encode, urlsafe_b64decode

def generate_key(password, salt):
    """Генерирует ключ шифрования на основе пароля и соли."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return key


def encrypt_message(message, key_int):
    """Шифрует сообщение с использованием AES-256-CBC."""
    # Генерация соли
    salt = os.urandom(16)
    # Генерация ключа из целого числа
    key = generate_key(str(key_int), salt)

    iv = os.urandom(16)  # Генерация случайного вектора инициализации
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(message.encode()) + padder.finalize()

    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # Возвращаем соль, вектор инициализации и зашифрованный текст в формате Base64
    return urlsafe_b64encode(salt + iv + ciphertext).decode()


def decrypt_message(message, key_int):
    """Расшифровывает сообщение, зашифрованное AES-256-CBC."""

    try:
        decoded_data = urlsafe_b64decode(message)
        salt = decoded_data[:16]
        iv = decoded_data[16:32]
        ciphertext = decoded_data[32:]
    except:
        raise ValueError("Invalid message format, unable to decode message.")

    # Генерация ключа из целого числа
    key = generate_key(str(key_int), salt)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    try:
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    except:
        raise ValueError("Invalid message or decryption key.")

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    try:
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
        return plaintext.decode()
    except:
        raise ValueError("Padding error during decryption.")