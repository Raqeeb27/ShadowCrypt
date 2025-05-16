""" Initializing database. """

import os
import sys
import json

from modules.aes import AESCipher
from modules.common_utils import get_dir_path, read_file, write_file
from modules.security_utils import get_verified_password


def main() -> None:
    """
    Main function that:
    - Encrypts mapping.db using a password provided by the user.
    - Writes the encrypted mapping data to a ".dll" file.
    - Reads app_path.json and writes it to a ".dll" file.

    The ".dll" file extension is used to store the database files to prevent 
    ransomware attacks from targeting and encrypting these critical files. 

    Output files:
    - enc_mapping.dll: Encrypted mapping data.
    - app_path.dll: Application path data (not encrypted).
    """
    dir_path = get_dir_path()
    aes = AESCipher()
    username = os.getlogin()

    # Read app_path.json
    app_path_data = read_file(os.path.join(dir_path, "db", "app_path.json"))
    updated_app_path_data = app_path_data.replace("USERNAME_PLACEHOLDER", username)
    app_path_json = json.loads(updated_app_path_data)

    invalid_paths = []
    for app, details in app_path_json.items():
        app_path = details.get("path")
        if not os.path.exists(app_path):
            print(f"Warning: Path for '{app}' does not exist: {app_path}")
            invalid_paths.append(app_path)
    if invalid_paths:
        print("\n[-] PATH ERROR")
    write_file(os.path.join(dir_path, "db", "app_path.dll"), updated_app_path_data)

    pw = get_verified_password()
    mapping_data = read_file(os.path.join(dir_path, "db", "mapping.db"))

    enc_mapping = aes.encrypt(mapping_data, pw)
    write_file(os.path.join(dir_path, "db", "enc_mapping.dll"), enc_mapping)

    # os.remove(f"{DIR_PATH}\\db\\mapping.db")
    # os.remove(f"{DIR_PATH}\\db\\app_path.json")


if __name__ == "__main__":
    main()
