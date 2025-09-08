"""
Database Initialization Script.

This script performs the following tasks:
- Encrypts the contents of "mapping.db" using a user-provided password.
- Writes the encrypted mapping data to "enc_<username>_mapping.dll" to help protect it from ransomware attacks.
- Encrypts "app_path.json" and writes it to "enc_app_path.dll".
- Warns the user if any application paths in "app_path.json" do not exist.
- Uses ".dll" file extensions for database files to reduce the risk of them being targeted by ransomware.

Modules used:
- AESCipher for encryption.
- Utility functions for file and path operations.
- Secure password input and validation.

Output files:
- db/enc_<username>_mapping.dll: Encrypted mapping database.
- db/enc_app_path.dll: Encrypted application path data.
"""

import os
import sys
import json
import time

try:
    from modules.aes import AESCipher
    from modules.common_utils import get_dir_path, read_file, write_file, hold_console_for_input
    from modules.security_utils import get_verified_password
except ImportError:
    print("\n[-] Import Error: Ensure that the script is run from the correct directory.\n\nExiting...\n")
    time.sleep(2)
    sys.exit(1)


def main(standalone=False) -> None:
    """
    Main function that:
    - Encrypts the 'mapping.db' file using a password provided by the user.
    - Writes the encrypted mapping data to a '.dll' file named 'enc_<username>_mapping.dll'.
    - Encrypts the 'app_path.json' file and writes it to 'enc_app_path.dll'.
    - Validates the existence of required files and checks for invalid application paths.
    - Warns the user about any invalid paths and unsupported extensions found in 'app_path.json'.

    The ".dll" file extension is used to store the database files to prevent 
    ransomware attacks from targeting and encrypting these critical files. 

    Args:
        standalone (bool, optional): If True, holds the console for user input on error. Defaults to False.
    Raises:
        SystemExit: If required files are not found in the expected directory.

    Output files:
    - enc_<username>_mapping.dll: Encrypted mapping data.
    - enc_app_path.dll: Encrypted application path data.
    """
    dir_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else get_dir_path()
    aes = AESCipher()

    if not os.path.exists(os.path.join(dir_path, "db", "app_path.json")) or not os.path.exists(os.path.join(dir_path, "db", "mapping.db")):
        print("\n[-] app_path.json or mapping.db file not found. Please ensure the script is run from the correct directory.")
        print("[-] FILE NOT FOUND")
        if standalone:
            hold_console_for_input()
        sys.exit(-2)

    app_path_data = read_file(os.path.join(dir_path, "db", "app_path.json"))
    app_path_json = json.loads(app_path_data)

    invalid_paths = []
    unsupported_extensions = []
    for app, details in app_path_json.items():
        app_path = details.get("path")
        if not os.path.exists(app_path):
            print(f"\nWarning: Path for '{app}' does not exist: {app_path}", end="")
            invalid_paths.append(app_path)
            unsupported_extensions.extend(details.get("ext", []))
    if invalid_paths:
        print(f"\n\n[-] This results in unsupported extensions:\n{unsupported_extensions}")

    pw = get_verified_password(validate_password=True, standalone=standalone)
    mapping_data = read_file(os.path.join(dir_path, "db", "mapping.db"))

    enc_mapping = aes.encrypt(mapping_data, pw)
    enc_app_path_data = aes.encrypt(app_path_data, pw)
    write_file(os.path.join(dir_path, "db", "enc_app_path.dll"), enc_app_path_data)
    username = os.getlogin()
    write_file(os.path.join(dir_path, "db", f"enc_{username}_mapping.dll"), enc_mapping)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "ShadowCrypt":
        print("\n[!] Warning: Running this file directly may overwrite the existing database resulting in data loss.\n**Recommended** - Recover all the hidden files first!\nProceed with caution!")
        main(standalone=True)
        print("\n[*] Database initialized successfully.")
        hold_console_for_input()
        sys.exit(0)
    main()
