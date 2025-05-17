"""
ShadowCrypt File Hider

This module provides functionality for securely hiding files by:
- Moving original files to hidden directories with obfuscated names.
- Storing mappings of original and hidden file paths in an encrypted database.
- Creating Windows shortcut (.lnk) files for easy access to hidden files.
- Synchronizing the access and modification times of shortcuts with the hidden files.
- Supporting multiple files and batch operations via command-line arguments.
- Validating file extensions and associating them with application icons.

Usage:
    python hiding.py --files <file1 file2 ...>  # Hide one or more files
    python hiding.py --testbed                  # Hide all files in the testbed folder

Notes:
    - Only supported file extensions can be hidden.
    - `.lnk` files cannot be hidden.
    - All mappings and sensitive data are stored securely using AES encryption.
"""

import os
import sys
import json
import time
import random
import argparse
from dataclasses import dataclass

from pylnk3 import for_file

from modules.aes import AESCipher
from modules.common_utils import get_dir_path, load_json, ext_to_app_path, move_file, process_filename_for_extension, hold_console_for_input
from modules.security_utils import hash_name, name_gen, load_encrypted_data, postprocessing


@dataclass
class MappingDB:
    """
    A data class to hold information in the enc_mapping.dll(mapping.db).

    Attributes:
        hidden_ext_list (list): List of supported file extensions for hiding.
        hidden_dir_dict (dict): Dictionary of hidden directories.
        mapping_dict (dict): Mapping of hidden file paths to their original names.
        hash_table (dict): Mapping of hashed names to hidden file paths.
    """
    hidden_ext_list: list
    hidden_dir_dict: dict
    mapping_dict: dict
    hash_table: dict


MAX_TRIES = 100
DIR_PATH = get_dir_path()
MAPPING_DB = MappingDB([], {}, {}, {})
APP_PATH_DB = load_json(os.path.join(DIR_PATH, "db", "app_path.dll"))


def preprocessing() -> dict[str, str]:
    """
    Prepares and validates the environment for file hiding.

    Returns:
        dict: A dictionary mapping file extensions to their corresponding icon paths.
    """
    for key in list(MAPPING_DB.hidden_dir_dict.keys()):
        if not os.path.exists(MAPPING_DB.hidden_dir_dict.get(key)):
            print(f"[-] {key} directory doesn't exist.")
            MAPPING_DB.hidden_dir_dict.pop(key)

    ext_icon_dict = {}
    for key in list(APP_PATH_DB.keys()):
        app = APP_PATH_DB.get(key)
        if not os.path.exists(app.get("path", "")):
            print(f"[-] {key} application doesn't exist.")
            APP_PATH_DB.pop(key)
        else:
            for ext in app.get("ext", []):
                ext_icon_dict[ext] = os.path.join(DIR_PATH, "icon", app.get("ico", ""))
    print(f"[*] Supported Extensions: {ext_icon_dict.keys()}\n")
    return ext_icon_dict


def make_shortcut(file_path: str, ext_icon_dict: dict[str, str],
                  hidden_dir_key: str = "") -> str | None:
    """
    Hides a file by creating a shortcut to it.

    Args:
        file_path (str): The path of the file to be hidden.
        ext_icon_dict (dict): Extension-to-icon mapping.
        hidden_dir_key (str): The key of the directory for hidden files.
                              If not provided or invalid, a random key is chosen.

    Returns:
        Optional[str]: The path of the hidden file, or None if hiding failed.
    """
    if not process_filename_for_extension(file_path):
        return None

    ext = file_path.split(".")[-1].lower()
    if ext not in ext_icon_dict:
        print(f"[-] Failed to hide {file_path}. Extension '.{ext}' is not supported.")
        return None

    app_path = ext_to_app_path(ext, APP_PATH_DB)
    if not app_path:
        print(f"[-] Failed to hide {file_path}. No application found for the extension: {ext}.")
        return None

    if hidden_dir_key and hidden_dir_key in MAPPING_DB.hidden_dir_dict:
        hidden_dir = MAPPING_DB.hidden_dir_dict[hidden_dir_key]
    else:
        hidden_dir = random.choice(list(MAPPING_DB.hidden_dir_dict.values()))

    if not os.path.exists(hidden_dir):
        print(f"[-] Hidden direcory does not exist: {hidden_dir}")
        return None

    for _ in range(MAX_TRIES):
        new_name = name_gen(MAPPING_DB.hidden_ext_list)
        hidden_file_path = os.path.join(hidden_dir, new_name)
        if not os.path.exists(hidden_file_path):
            break
    else:
        print("[-] Exceeded max tries for unique filename.")
        return None

    hashed_name = hash_name(hidden_file_path)
    shortcut_path = f"{file_path}.lnk"

    file_name, file_ext = os.path.splitext(file_path)
    count = 1
    while os.path.exists(shortcut_path):
        shortcut_path = f"{file_name}({count}){file_ext}.lnk"
        count += 1

    try:
        move_status = move_file(file_path, hidden_file_path)
        if not move_status:
            return None

        # executable (for release)
        if getattr(sys, "frozen", False):
            target_path = os.path.join(DIR_PATH, "dist", "ShadowCrypt.exe")
            arguments = f"link --hash {hashed_name}"
        # python script (for test)
        else:
            target_path = sys.executable
            arguments = f"\"{os.path.join(DIR_PATH, 'linker.py')}\" --hash {hashed_name}"

        # Create a shortcut (.lnk) file using pylnk3 library
        for_file(
            lnk_name=shortcut_path,
            target_file=target_path,
            arguments=arguments,
            icon_file=ext_icon_dict.get(ext, ""),
        )

        MAPPING_DB.mapping_dict[hidden_file_path] = file_path
        MAPPING_DB.hash_table[hashed_name] = hidden_file_path

        print(f"  [+] Hiding success: {file_path} -> {hidden_file_path}")
        return hidden_file_path

    except (ValueError, OSError) as e:
        print(f"[-] Failed to hide {file_path}: {e}")
        if os.path.exists(hidden_file_path):
            move_file(hidden_file_path, file_path)
        return None


def synchronize(target_list: list[str], mapping_dict: dict[str, str]) -> None:
    """
    Synchronizes hidden files with their corresponding shortcuts.

    Args:
        target_list (list): List of hidden file paths.
        mapping_dict (dict): Mapping of hidden files to their original files.
    """
    for hidden_file in target_list:
        original_file = mapping_dict.get(hidden_file)
        shortcut_path = f"{original_file}.lnk"
        if os.path.exists(hidden_file) and os.path.exists(shortcut_path):
            file_st = os.stat(hidden_file)
            os.utime(shortcut_path, (file_st.st_atime, file_st.st_mtime))


def main(is_test: bool = False, files: list[str] = None) -> None:
    """
    Main function to hide files by creating shortcuts and managing file mappings.

    Args:
        is_test (bool): Whether to hide all files in the testbed folder.
        files (list[str]): List of file paths to hide.
    """
    aes = AESCipher()

    enc_mapping_filepath = os.path.join(DIR_PATH, "db", "enc_mapping.dll")
    raw_data, pw = load_encrypted_data(enc_mapping_filepath, aes, prompt="PASSWORD? : ")
    data = json.loads(raw_data.replace("'", '"'))

    MAPPING_DB.hidden_ext_list = data["hidden_ext"]
    MAPPING_DB.hidden_dir_dict = data["hidden_dir"]
    MAPPING_DB.mapping_dict = data["mapping_table"]
    MAPPING_DB.hash_table = data["hash_table"]

    ext_icon_dict = preprocessing()

    target_list = []
    if is_test:
        testbed_path = os.path.join(DIR_PATH, "testbed")
        for file in os.listdir(testbed_path):
            file = os.path.join(testbed_path, file)
            if file.endswith(".lnk"):
                continue
            # "help" is hardcoded as the hidden_dir_key for testing purposes
            target_list.append(make_shortcut(file, ext_icon_dict, hidden_dir_key="help"))

    elif files:
        for file in files:
            if file.endswith(".lnk"):
                print(f"[-] Error {file}: .lnk file cannot be hidden.")
                continue
            if not (os.path.exists(file) and os.path.isfile(file)):
                print(f"[-] Invalid File: '{file}' does not exist or is not a file.")
                continue
            target_list.append(make_shortcut(file, ext_icon_dict))

    target_list = [item for item in target_list if item is not None]
    if len(target_list) == 0:
        if is_test:
            print("[-] No files to hide in testbed folder.")
        elif files:
            print("[-] No valid files selected to hide.")
        hold_console_for_input()
        sys.exit(1)

    data["mapping_table"] = MAPPING_DB.mapping_dict
    data["hash_table"] = MAPPING_DB.hash_table
    postprocessing(data, aes, pw, enc_mapping_filepath)
    synchronize(target_list, MAPPING_DB.mapping_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="+", help="Hide multiple files (provide full paths)")
    parser.add_argument("--testbed", action="store_true", help="Hide all files in testbed folder")
    args = parser.parse_args()

    if not (args.testbed or args.files):
        print("\n[-] No arguments provided.")
        f = "ShadowCrypt.exe hide" if getattr(sys, 'frozen', False) else "hiding.py"
        print(f"[*] Usage: {f} --files <file1 file2 ...> OR --testbed")
        hold_console_for_input()
        sys.exit(1)

    if sum([bool(args.testbed), bool(args.files)]) > 1:
        print("\n[-] Only one of --files OR --testbed can be used at a time.")
        hold_console_for_input()
        sys.exit(1)

    if args.testbed:
        if not os.path.exists(os.path.join(DIR_PATH, "testbed")):
            print("\n[-] Testbed folder does not exist.")
            hold_console_for_input()
            sys.exit(1)

        print("[*] Hiding all files in testbed folder.\n")

    elif args.files:
        if not any(os.path.isfile(file) for file in args.files):
            print("\n[-] Invalid file paths provided. Some files do not exist or are not valid files.")
            hold_console_for_input()
            sys.exit(1)
        if all(file.endswith(".lnk") for file in args.files):
            print("\n[-] Invalid file paths provided. `.lnk` files cannot be hidden.")
            hold_console_for_input()
            sys.exit(1)
        print("\n[*] Hiding files:")
        print("\n".join(args.files),"\n")

    main(args.testbed, args.files)
    time.sleep(1)
