"""
This module handles the mapping and execution of files based on hashed names.
It retrieves application paths and mapping data to execute files securely 
via shortcuts. This helps in linking hidden files to their respective applications.

Usage:
    python linker.py --hash <hashed_filename>
"""

import os
import sys
import json
import argparse
import subprocess

from modules.aes import AESCipher
from modules.common_utils import get_dir_path, load_json, ext_to_app_path
from modules.security_utils import load_encrypted_data


def main(hashed_name: str) -> None:
    """
    Main function to link and open a file based on its hash name.

    This function retrieves file mapping and application path data from encrypted
    and JSON files. It then identifies the appropriate application to open the file
    based on its extension and executes the corresponding command.

    Args:
        hashed_name (str): The hash name of the file to be opened.

    Raises:
        SystemExit: If the provided hash name or its mapping is not found,
                    or if no application is mapped for the file's extension.
    """
    dir_path = get_dir_path()
    aes = AESCipher()

    app_path_dict = load_json(os.path.join(dir_path, "db", "app_path.dll"))

    enc_mapping_filepath = os.path.join(dir_path, "db", "enc_mapping.dll")
    raw_data, _ = load_encrypted_data(enc_mapping_filepath, aes, prompt="PASSWORD? : ")
    data = json.loads(raw_data.replace("'", '"'))
    mapping_dict = data["mapping_table"]
    hash_table = data["hash_table"]

    if hashed_name not in hash_table:
        print("[-] Provided file hash name not found.")
        sys.exit(1)

    hidden_name = hash_table[hashed_name]
    if not os.path.exists(hidden_name):
        print("[-] Hidden file does not exist.")
        sys.exit(1)

    if hidden_name not in mapping_dict:
        print("[-] Mapping for hidden file not found.")
        sys.exit(1)

    file_name = mapping_dict[hidden_name]
    ext = file_name.split(".")[-1]
    app = ext_to_app_path(ext, app_path_dict)
    if not app:
        print("[-] No application mapped for the file extension.")
        sys.exit(1)

    try:
        with open(hidden_name, "rb") as f:
            pass
    except PermissionError as e:
        print(f"\n[!] Failed to open {hidden_name}: File is in use by another process.")
        print("[!] Please close the file and try again.\n")
        sys.exit(1)

    if ext in app_path_dict.get("photo", {}).get("ext", []):
        arg = app_path_dict["photo"].get("arg", "")
        cmd = f"{app} {arg} {hidden_name}"
    else:
        cmd = [app, hidden_name]

    print("[*] Executing command:", cmd)
    subprocess.Popen(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Link file via hashed filename.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--hash", required=True, help="Hashed filename")
    args = parser.parse_args()

    print("[*] Opening the file...\n")

    main(hashed_name=args.hash)
