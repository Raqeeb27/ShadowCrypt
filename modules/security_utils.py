"""
Security-related utility functions.

This module provides functions for hashing, generating random file names,
validating and verifying passwords, encrypting and decrypting data, and
postprocessing encrypted data.

Functions:
- hash_name: Generates a SHA-1 hash for a given string.
- name_gen: Creates unique file names with obfuscated extensions.
- check_password_requirements: Validates a password against specific requirements.
- get_verified_password: Prompts the user for a password with optional confirmation.
- load_encrypted_data: Decrypts and loads data from an encrypted file.
- postprocessing: Encrypts and writes mapping data to a file.
"""

import sys
import json
import time
import random
import string
import hashlib
import getpass

from modules.aes import AESCipher
from modules.common_utils import read_file, write_file


MAX_ATTEMPTS = 3
MIN_PW_LEN = 8
MAX_PW_LEN = 20
WAIT_TIME = 1


def hash_name(name: str) -> str:
    """
    Generates a SHA-1 hash for a given string.

    Args:
        name (str): The input string to hash.

    Returns:
        str: The hexadecimal SHA-1 hash of the input string.
    """
    sha = hashlib.new("sha1")
    sha.update(name.encode())
    return sha.hexdigest()


def name_gen(hidden_ext_list: list[str], length: int = 8) -> str:
    """
    Generates a random file name with a random extension from the provided list.

    Args:
        hidden_ext_list (list): A list of possible file extensions.
        length (int): The length of the randomly generated name (default is 8).

    Returns:
        str: A randomly generated file name with an extension.
    """
    name = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    ext = random.choice(hidden_ext_list)
    return f"{name}.{ext}"


def check_password_requirements(pw: str) -> list[str]:
    """
    Checks the password against a set of requirements and returns unmet requirements.

    Args:
        pw (str): The password to check.

    Returns:
        list[str]: A list of unmet password requirements.
    """
    unmet_pw_reqs = []
    if len(pw) < MIN_PW_LEN:
        unmet_pw_reqs.append(f"PASSWORD must be at least {MIN_PW_LEN} characters long.")
    if not any(char.isdigit() for char in pw):
        unmet_pw_reqs.append("PASSWORD must contain at least one digit.")
    if not any(char.islower() for char in pw):
        unmet_pw_reqs.append("PASSWORD must contain at least one lowercase letter.")
    if not any(char.isupper() for char in pw):
        unmet_pw_reqs.append("PASSWORD must contain at least one uppercase letter.")
    if not any(char in string.punctuation for char in pw):
        unmet_pw_reqs.append("PASSWORD must contain at least one special character.")
    if not all(char.isalnum() or char in string.punctuation for char in pw):
        unmet_pw_reqs.append("PASSWORD must only contain letters, numbers, and special characters.")
    if len(pw) > MAX_PW_LEN:
        unmet_pw_reqs.append(f"PASSWORD must be at most {MAX_PW_LEN} characters long.")
    return unmet_pw_reqs


def get_verified_password(validate_password=False) -> str:
    """
    Prompts the user to enter and confirm a password, validates it against 
    specific requirements, and returns the verified password.

    Args:
        validate_password (bool): If True, the password will be validated against 
                                  specific requirements.
    Returns:
        str: The verified password if it meets all requirements.

    Raises:
        SystemExit: If the user interrupts the process or if the password 
                    validation fails.
    """
    try:
        pw = getpass.getpass("Create new PASSWORD: ")
        pw2 = getpass.getpass("\nConfirm PASSWORD: ")

        if not pw or pw != pw2:
            print("\n[-] PASSWORD mismatch or empty. Please try again.")
            raise ValueError("\n[-] PASSWORD ERROR")
        if validate_password:
            unmet_pw_reqs = check_password_requirements(pw)
            if unmet_pw_reqs:
                print("\n[!] PASSWORD does not meet the following requirements:")
                for req in unmet_pw_reqs:
                    print(f"  - {req}")
                raise ValueError("\n[-] PASSWORD ERROR")
        return pw

    except (KeyboardInterrupt, EOFError):
        print("\n\n[-] Keyboard Interrupt")
        sys.exit(-2)
    except ValueError as e:
        print(e)
        sys.exit(1)


def load_encrypted_data(filepath: str, aes: AESCipher,
                        prompt: str = "PASSWORD? : ") -> tuple[str, str]:
    """
    Loads and decrypts encrypted data from a file using a password.

    Args:
        filepath (str): Path to the encrypted file.
        aes (AESCipher): An instance of the AES cipher for decryption.
        prompt (str): The prompt to display for password input.

    Returns:
        Tuple[str, str]: Decrypted data and the password.

    Raises:
        SystemExit: If decryption fails after maximum attempts.
    """
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        try:
            pw = getpass.getpass(prompt)
        except (KeyboardInterrupt, EOFError):
            print("\n[!] Keyboard Interrupt")
            sys.exit(1)
        data = read_file(filepath)
        try:
            dec_data = aes.decrypt(data, pw)
            if "hidden_ext" in dec_data or "mapping_table" in dec_data:
                return dec_data, pw
        except UnicodeDecodeError:
            attempts += 1
            print(f"\n[-] PASSWORD Fail :(\n{MAX_ATTEMPTS - attempts} attempts remaining\n")
            if attempts <= MAX_ATTEMPTS:
                time.sleep(WAIT_TIME)
        except (ValueError, OSError, TypeError) as e:
            print(f"[-] Decryption error: {e}")
            sys.exit(1)

    print(f"Maximum password attempts ({MAX_ATTEMPTS}) exceeded.")
    sys.exit(1)


def postprocessing(data_dict: dict[str, str | list], aes, pw: str, db_filepath: str) -> None:
    """
    Encrypts and writes a dictionary to a specified file path.

    Args:
        data_dict (dict): The dictionary to encrypt and write.
        aes: An instance of the AES cipher for encryption.
        pw (str): The password used for encryption.
        db_filepath (str): The file path where the encrypted data will be stored.

    Returns:
        None
    """
    enc_data = aes.encrypt(json.dumps(data_dict), pw)
    write_file(db_filepath, enc_data)
