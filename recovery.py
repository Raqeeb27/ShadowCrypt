"""
This module handles the recovery of files that were previously hidden.
It renames obfuscated files back to their original names and removes
associated shortcuts.

Usage:
    python recovery.py --hash <hashed_filename>         # Recover a file using its hashed_filename
    python recovery.py --link_file_path <shortcut.lnk>  # Recover a file using its shortcut
    python recovery.py --all                            # Recover all hidden files
"""

import os
import sys
import json
import time
import argparse

import pylnk3

from pathlib import Path
from modules.aes import AESCipher
from modules.common_utils import get_dir_path, move_file, process_filename_for_extension
from modules.security_utils import hash_name, postprocessing, load_encrypted_data


def process_link_file(link_file_path: str, verbose: bool = True) -> str | None:
    """
    Processes a .lnk shortcut file to extract the hashed name.

    Args:
        link_file_path (str): Path of the shortcut file.
        verbose (bool): Whether to print error messages or not.

    Returns:
        str | None: Extracted hashed name from the shortcut file, or None if an error occurs.

    Raises:
        ValueError: If the shortcut file is invalid or missing a hash.
        pylnk3.FormatException: If the shortcut file format is invalid.
    """
    try:
        lnk = pylnk3.parse(str(link_file_path))
        if not lnk.arguments:
            raise ValueError("Missing arguments in shortcut.")
        if not len(lnk.arguments.split()) in [2, 3]:
            raise ValueError("Missing hash in shortcut.")
        if lnk.arguments.split()[-2].startswith("--hash"):
            return lnk.arguments.split()[-1]
        else:
            raise ValueError("Invalid or missing hash in shortcut.")
    except (OSError, ValueError, pylnk3.FormatException) as e:
        if verbose:
            print(f"\n[!] Error processing shortcut {link_file_path}: {e}")
    return None


def search_lnk_files(directory: Path, recursive: bool = True, excluded_paths: list[str] = None) -> list:
    """
    Searches for .lnk files in the specified directory.

    Args:
        directory (Path): The directory to search for .lnk files.
        recursive (bool): Whether to search recursively or not.
        excluded_paths (list[Path]): A list of paths to exclude from the search.

    Returns:
        list: A list of paths to .lnk files found in the directory.
    """
    try:
        directory = Path(directory)
        excluded_paths = excluded_paths or []
        lnk_files = [str(file) for file in directory.iterdir() if file.is_file() and file.suffix == ".lnk"]
        lnk_files = [f for f in lnk_files if f is not None]
        if not recursive:
            return lnk_files
        directories = [str(d) for d in directory.iterdir() if d.is_dir()]
        directories = [d for d in directories if d is not None]
        if directories:
            for dir in directories:
                if any(dir.startswith(excluded) for excluded in excluded_paths):
                    continue
                for path in Path(dir).rglob("*.lnk"):
                    if any(str(path).startswith(excluded) for excluded in excluded_paths):
                        continue
                    lnk_files.append(str(path))
        return lnk_files
    except (KeyboardInterrupt, EOFError):
        print("\n[!] Search interrupted by user.")
        sys.exit(1)
    except (OSError, ValueError) as e:
        print(f"[!] Error while searching for .lnk files in {directory}: {e}")
        return []


def find_lnks_with_hash() -> list[str] | None:
    """
    Searches for .lnk files with '--hash' in their target arguments across drives.

    Returns:
        list[str] | None: Paths to matching .lnk files, or None if none are found.
    Notes:
        - Excludes "AppData" from the home directory search.
        - Dynamically scans drives D: to Z: and the user's home directory.
    """
    print("[*] Searching for all link files to recover....\n")
    try:
        user_home_dir = Path.home()
        appdata_path = user_home_dir / "AppData"
        testbed_path = os.path.join(get_dir_path(), "testbed")

        drives = [Path(f"{drive}:\\") for drive in "DEFGHIJKLMNOPQRSTUVWXYZ" if Path(f"{drive}:\\").exists()]
        if user_home_dir.exists():
            drives.insert(0, user_home_dir)

        lnks_with_hash = []

        for drive in drives:
            if drive == user_home_dir:
                lnks_to_search = search_lnk_files(drive, recursive=True, excluded_paths=[str(appdata_path), testbed_path])
            else:
                lnks_to_search = search_lnk_files(drive, recursive=True, excluded_paths=[testbed_path])

            if not lnks_to_search:
                continue

            for lnk_file in lnks_to_search:
                try:
                    lnk = pylnk3.parse(lnk_file)
                    if lnk.arguments and "--hash" in lnk.arguments:
                        lnks_with_hash.append(lnk_file)
                except (OSError, IndexError, pylnk3.FormatException):
                    continue

        if lnks_with_hash:
            return lnks_with_hash
        else:
            print("[-] No .lnk files with '--hash' in their target were found.")
    except (KeyboardInterrupt, EOFError):
        print("\n[!] Search interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print("[!] An error occurred: \n", e)
    return None


def recover_valid_found_links(lnks_to_search: list, hash_table: dict[str, str], 
                            mapping_dict: dict[str, str]) -> None:
    """
    Recovers files based on the provided list of .lnk files.

    Args:
        lnks_to_search (list): List of .lnk file paths to process.
        hash_table (dict[str, str]): Mapping of hashed names to hidden file paths.
        mapping_dict (dict[str, str]): Mapping of hidden file paths to their original file paths.

    Returns:
        None: Performs recovery operations and updates the hash_table and mapping_dict in place.
    """
    recovered_files = 0
    for lnk_file in lnks_to_search:
        hashed_name = process_link_file(lnk_file, verbose=False)
        hidden_file = hash_table.get(hashed_name)
        if not hidden_file:
            continue
        recovered = recovery(hidden_file, mapping_dict, hash_table, lnk_file)
        if recovered:
            recovered_files += 1

    if recovered_files == 0:
        print("[-] No valid lnk files found to recover.")


def recovery(hidden_file: str, mapping_dict: dict[str, str],
             hash_table: dict[str, str], shortcut_file_path: str | None = None) -> bool | None:
    """
    Recovers a hidden file to its original location and removes its associated shortcut.

    Args:
        hidden_file (str): Path to the hidden file.
        mapping_dict (dict[str, str]): Mapping of hidden file paths to their original file paths.
        hash_table (dict[str, str]): Mapping of hashed names to hidden file paths.
        shortcut_file_path (str | None): Path of the shortcut file for restoring the original file.
    """
    try:
        if shortcut_file_path:
            original_file = shortcut_file_path.removesuffix(".lnk").strip()
            original_file = process_filename_for_extension(original_file)
            if not original_file:
                return None
        else:
            original_file = mapping_dict.get(hidden_file)

        if not original_file:
            raise ValueError(f"No mapping found for {hidden_file}.")

        original_name, original_ext = os.path.splitext(original_file)
        count = 1
        while os.path.exists(original_file):
            original_file = f"{original_name}({count}){original_ext}"
            count += 1

        move_status = move_file(hidden_file, original_file)
        if not move_status:
            return None

        shortcut_path = f"{original_name}{original_ext}.lnk"
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)

        mapping_dict.pop(hidden_file, None)
        h_name = hash_name(hidden_file)
        hash_table.pop(h_name, None)
        print(f"  [+] Recovered: {hidden_file} -> {original_file}")
        return True

    except (ValueError, OSError) as e:
        print(f"  [-] Failed to recover {hidden_file}: {e}")
        return None


def main(hashed_name: str | None = None, files: list | None = None,
         recover_all: bool | None = False, dir_path: str | None = None, recursive: bool | None = False) -> None:
    """
    Main function to recover hidden files based on their hash, recover all hidden files,
    or recover files in the testbed directory.

    Args:
        hashed_name (str): The hashed name of the file to recover.
        shortcut_file_path (str): Path of the shortcut file for restoring the original file.
        recover_all (bool): Flag to indicate recovery of all hidden files.
        testbed (bool): Flag to indicate recovery of files in the testbed directory.
    """
    aes = AESCipher()

    enc_mapping_filepath = os.path.join(get_dir_path(), "db", "enc_mapping.dll")
    raw_data, pw = load_encrypted_data(enc_mapping_filepath, aes, prompt="PASSWORD? : ")
    data = json.loads(raw_data.replace("'", '"'))

    mapping_dict = data.get("mapping_table")
    hash_table = data.get("hash_table")

    if not mapping_dict:
        print("[-] No hidden files to recover.")
        sys.exit(1)

    if dir_path:
        lnks_to_search = search_lnk_files(dir_path, recursive=recursive)
        if not lnks_to_search:
            if os.path.basename(dir_path) == "testbed":
                dir_path = "testbed"
            print(f"[-] No .lnk files found in {dir_path}.")
            sys.exit(1)
        recover_valid_found_links(lnks_to_search, hash_table, mapping_dict)

    elif recover_all:
        found_lnk_files = find_lnks_with_hash()
        if not found_lnk_files:
            print("\n[*] Recovering all hidden files to the original paths.")
            hidden_files = list(mapping_dict.keys())
            for hidden_file in hidden_files:
                recovered = recovery(hidden_file, mapping_dict, hash_table)
                if not recovered:
                    print(f"[-] Failed to recover {hidden_file}.")
        else:
            recover_valid_found_links(found_lnk_files, hash_table, mapping_dict)

    elif files:
        for file_path in files:
            if not (os.path.isfile(file_path) and file_path.lower().endswith(".lnk")):
                print(f"[!] Invalid shortcut file: {file_path}")
                continue
            original_file = file_path.removesuffix(".lnk").strip()
            if not process_filename_for_extension(original_file):
                continue
            hashed_name = process_link_file(file_path)
            if not hashed_name:
                continue

            if hashed_name in hash_table:
                hidden_file = hash_table.get(hashed_name)
                recovered = recovery(hidden_file, mapping_dict, hash_table, file_path)
                if not recovered:
                    print(f"[-] Failed to recover {hidden_file}.")
            else:
                print("[-] Provided hash not found.")
                continue

    data["mapping_table"] = mapping_dict
    data["hash_table"] = hash_table
    postprocessing(data, aes, pw, enc_mapping_filepath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hash", type=str, help="Recover specific file using its hash.")
    parser.add_argument("--link_files", nargs="+", help="Recover multiple files (provide full paths)")
    parser.add_argument("--all", action="store_true", help="Recover all hidden files.")
    parser.add_argument("--testbed", action="store_true", help="Recover all .lnk files in the testbed directory.")
    parser.add_argument("--dir", type=str, help="Recover all hidden files in the specified directory. Use -R for recursive search.")
    parser.add_argument("-R", "--recursive", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()

    if not any([args.hash, args.link_files, args.all, args.testbed, args.dir]):
        print("[-] No arguments provided.")
        print("[*] Usage: recover.py --all OR --hash <hash>\nOR --link_file_path <link_file_path> OR --testbed OR --dir <dir_path>")
        sys.exit(1)

    if sum([bool(args.hash), bool(args.link_files), bool(args.all), bool(args.testbed), bool(args.dir)]) > 1:
        print("[-] Only one of --all, --hash, --link_file_path, --testbed or --dir can be used at a time.")
        sys.exit(1)

    if args.recursive and not args.dir:
        print("[-] The -R/--recursive option can only be used with --dir.")
        sys.exit(1)

    if args.hash:
        print(f"[+] Recovering file with hash: {args.hash}\n")

    elif args.link_files:
        if not all(os.path.isfile(file) for file in args.link_files):
            print("[-] Invalid file paths provided. Some files do not exist or are not valid files.")
            sys.exit(1)
        if not all(file.endswith(".lnk") for file in args.link_files):
            print("[-] Invalid file paths provided. Only `.lnk` files can be recovered.")
            sys.exit(1)
        print("\n[+] Recovering files: ")
        print("\n".join(args.link_files),"\n")

    elif args.all:
        print("[*] Recovering all hidden files...\nThis may take a while.\n")

    elif args.testbed:
        args.dir = os.path.join(get_dir_path(), "testbed")
        args.recursive = False
        print("[*] Recovering all .lnk files in the testbed directory...\n")

    elif args.dir:
        args.dir = os.path.abspath(args.dir)
        args.dir = args.dir[:-2] if args.dir.endswith(":\\\"") else args.dir
        if not (os.path.isdir(args.dir) and os.path.exists(args.dir)):
            print(f"\n[!] Invalid directory: {args.dir}")
            sys.exit(1)
        if args.recursive:
            print(f"[*] Recovering all hidden files in {args.dir} and its subdirectories...\n")
        else:
            print(f"[*] Recovering all hidden files in the directory: {args.dir}\n")

    main(args.hash, args.link_files, args.all, args.dir, args.recursive)
    time.sleep(1)
