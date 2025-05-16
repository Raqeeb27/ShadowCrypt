"""
AES Cipher Module
This module provides the `AESCipher` class for symmetric encryption and decryption using the AES algorithm in CBC mode.
Keys are derived from passwords using SHA-256, and data is padded using PKCS#7-style padding.
Classes:
    AESCipher: 
        Provides methods for encrypting and decrypting strings with AES-256 using password-based key derivation.
Usage Example:
    cipher = AESCipher()
    encrypted = cipher.encrypt("my secret message", "password123")
    decrypted = cipher.decrypt(encrypted, "password123")
"""

from hashlib import sha256

from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    """
    A class for AES encryption and decryption using a password-derived key.

    Attributes:
        bs (int): Block size for AES encryption (32 bytes for AES-256).
    """

    def __init__(self) -> None:
        """
        Initializes the AESCipher class with padding and unpadding functions.
        """
        self.bs = 32
        self.pad = lambda s: s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
        self.unpad = lambda s: s[:-ord(s[-1])]

    def pass2key(self, pw: str) -> bytes:
        """
        Derives a 256-bit key from a password using SHA-256.

        Args:
            pw (str): The password to derive the key from.

        Returns:
            bytes: A 256-bit key derived from the password.
        """
        return sha256(pw.encode()).digest()

    def encrypt(self, raw: str, pw: str) -> str:
        """
        Encrypts a plaintext string using AES in CBC mode.

        Args:
            raw (str): The plaintext to encrypt.
            pw (str): The password for key derivation.

        Returns:
            str: The encrypted data in hexadecimal format.
        """
        raw_padded = self.pad(raw).encode()
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.pass2key(pw), AES.MODE_CBC, iv)
        encrypted_data = iv + cipher.encrypt(raw_padded)
        return encrypted_data.hex()

    def decrypt(self, enc: str, pw: str) -> str:
        """
        Decrypts an AES-encrypted string in hexadecimal format.

        Args:
            enc (str): The encrypted data in hexadecimal format.
            pw (str): The password for key derivation.

        Returns:
            str: The decrypted plaintext.
        """
        enc_bytes = bytes.fromhex(enc)
        iv = enc_bytes[:AES.block_size]
        cipher = AES.new(self.pass2key(pw), AES.MODE_CBC, iv)
        decrypted_data = cipher.decrypt(enc_bytes[AES.block_size:])
        return self.unpad(decrypted_data.decode())
