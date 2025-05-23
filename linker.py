"""
ShadowCrypt File Linker

This script allows you to open files using their hashed names.
It securely retrieves file mappings and application associations, then launches
the appropriate application to open the hidden file.

Usage:
    python linker.py --hash <hashed_filename>

Arguments:
    --hash    The hash name of the file to be opened.

The script ensures that only mapped and existing files are opened, and
handles errors such as missing mappings, missing files, or missing application associations.
"""

import os
import sys
import time
import argparse
import subprocess

try:
    from modules.aes import AESCipher
    from modules.common_utils import ext_to_app_path, hold_console_for_input, check_db_files
    from modules.security_utils import load_encrypted_data
except ImportError:
    print("\n[-] Import Error: Ensure that the script is run from the correct directory.\n\nExiting...\n")
    time.sleep(2)
    sys.exit(1)


def main(hashed_name: str) -> None:
    """
    Main function to link and open a file based on its hash name.

    This function retrieves file mapping and application association data from encrypted
    files. It identifies the original filename and the appropriate application to open
    the file based on its extension, then launches the application with the hidden file.

    Args:
        hashed_name (str): The hash name of the file to be opened.

    Exits:
        If the provided hash name, its mapping, the hidden file, or the application association
        is not found, or if the file cannot be opened.
    """
    aes = AESCipher()

    enc_mapping_filepath, enc_app_path_filepath = check_db_files()

    mapping_data, pw = load_encrypted_data(enc_mapping_filepath, aes, prompt="PASSWORD? : ")
    app_path_data = load_encrypted_data(enc_app_path_filepath, aes, passwd=pw)

    mapping_dict = mapping_data.get("mapping_table")
    hash_table = mapping_data.get("hash_table")

    if hashed_name not in hash_table:
        print("[-] Provided file hash name not found.")
        hold_console_for_input()
        sys.exit(1)

    hidden_name = hash_table[hashed_name]
    if not os.path.exists(hidden_name):
        print("[-] Hidden file for the provided hash name not found.")
        hold_console_for_input()
        sys.exit(1)

    if hidden_name not in mapping_dict:
        print("[-] Mapping for hidden file not found.")
        hold_console_for_input()
        sys.exit(1)

    file_name = mapping_dict[hidden_name]
    ext = file_name.split(".")[-1]
    app = ext_to_app_path(ext, app_path_data)
    if not app:
        print(f"[-] No application mapped for the file extension `{ext}`")
        hold_console_for_input()
        sys.exit(1)

    try:
        with open(hidden_name, "rb") as f:
            pass
    except PermissionError as e:
        print(f"\n[!] Failed to open {hidden_name}: File is in use by another process.")
        print("[!] Please close the file and try again.\n")
        hold_console_for_input()
        sys.exit(1)

    if ext in app_path_data.get("photo", {}).get("ext", []):
        arg = app_path_data["photo"].get("arg", "")
        cmd = f"{app} {arg} {hidden_name}"
    else:
        cmd = [app, hidden_name]

    print("[*] Executing command:", cmd)
    try:
        subprocess.Popen(cmd)
    except Exception as e:
        print(f"\n[!] Failed to launch application: {e}")
        hold_console_for_input()
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Link file via hashed filename.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--hash", help="Hashed filename")

    try:
        args = parser.parse_args()

        if not args.hash:
            print("\n[-] No hash provided.")
            f = "ShadowCrypt.exe link" if getattr(sys, 'frozen', False) else "linker.py"
            print(f"[*] Usage: {f} --hash <hashed_filename>")
            hold_console_for_input()
            sys.exit(1)

        print("\n[*] Opening the file...\n")
        main(hashed_name=args.hash)

    except (KeyboardInterrupt, EOFError):
        print("\n\n[-] Keyboard Interrupt")
        hold_console_for_input()
        sys.exit(1)
