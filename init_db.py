"""Initializing database.

This script initializes the application's database by:
- Encrypting the contents of "mapping.db" using a password provided by the user.
- Writing the encrypted mapping data to "enc_<username>_mapping.dll" to help protect it from ransomware attacks.
- Warning the user if any application paths in "app_path.json" do not exist.
- Using ".dll" file extensions for database files to reduce the risk of them being targeted by ransomware.

Modules used:
- AESCipher for encryption.
- Utility functions for file and path operations.
- Secure password input and validation.

Output files:
- db/enc_<username>_mapping.dll: Encrypted mapping database.
- db/app_path.dll: Application path data (not encrypted).
"""

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
    dir_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else get_dir_path()
    aes = AESCipher()

    app_path_data = read_file(os.path.join(dir_path, "db", "app_path.json"))
    app_path_json = json.loads(app_path_data)

    invalid_paths = []
    for app, details in app_path_json.items():
        app_path = details.get("path")
        if not os.path.exists(app_path):
            print(f"Warning: Path for '{app}' does not exist: {app_path}")
            invalid_paths.append(app_path)
    if invalid_paths:
        print("\n[-] PATH ERROR")
    write_file(os.path.join(dir_path, "db", "app_path.dll"), app_path_data)

    pw = get_verified_password(validate_password=True)
    mapping_data = read_file(os.path.join(dir_path, "db", "mapping.db"))

    enc_mapping = aes.encrypt(mapping_data, pw)
    username = os.getlogin()
    write_file(os.path.join(dir_path, "db", f"enc_{username}_mapping.dll"), enc_mapping)


if __name__ == "__main__":
    full_command = " ".join(sys.argv)
    if full_command.find("ShadowCrypt") == -1:
        print("\n[!] Warning: Running this file directly may overwrite the existing database resulting in data loss.\n**Recommended** - Recover all the hidden files first!\nProceed with caution!")
    main()
