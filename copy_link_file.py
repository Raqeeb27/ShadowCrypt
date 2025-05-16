import argparse
import os
import json
import random
import string
import sys
import pylnk3

from modules.aes import AESCipher
from modules.security_utils import hash_name, name_gen, postprocessing, load_encrypted_data
from modules.common_utils import get_dir_path, read_file, write_file, move_file
import shutil

def copy_link_file(link_file_path: str) -> None:
    """
    Extracts the hash value from the link file, finds the corresponding hidden file,
    creates a copy of it with a random filename, updates the mapping table and hash table,
    and modifies the link file to point to the new hash.

    Args:
        link_file_path (str): Path to the .lnk shortcut file.

    Returns:
        None
    """
    try:
        # Parse the link file to extract the hash
        lnk = pylnk3.parse(link_file_path)
        if not lnk.arguments or not lnk.arguments.split()[-2].startswith("--hash"):
            raise ValueError("Invalid or missing hash in shortcut.")
        original_hash = lnk.arguments.split()[-1]

        # Load encrypted database
        aes = AESCipher()
        enc_mapping_filepath = os.path.join(get_dir_path(), "db", "enc_mapping.dll")
        raw_data, pw = load_encrypted_data(enc_mapping_filepath, aes, prompt="PASSWORD? : ")
        data = json.loads(raw_data.replace("'", '"'))

        mapping_table = data.get("mapping_table", {})
        hash_table = data.get("hash_table", {})

        # Find the hidden file corresponding to the hash
        hidden_file_path = hash_table.get(original_hash)
        if not hidden_file_path or not os.path.exists(hidden_file_path):
            raise FileNotFoundError(f"Hidden file for hash {original_hash} not found.")

        # Generate a random filename for the copy
        hidden_dir = os.path.dirname(hidden_file_path)
        new_hidden_file_name = name_gen(data.get("hidden_ext", []))
        new_hidden_file_path = os.path.join(hidden_dir, new_hidden_file_name)

        # Copy the hidden file
        shutil.copy2(hidden_file_path, new_hidden_file_path)

        # Generate a new hash for the copied file
        new_hash = hash_name(new_hidden_file_path)
        lnk.arguments = lnk.arguments.replace(original_hash, new_hash)

        link_file_path = link_file_path.removesuffix(".lnk").strip()

        # Update the link file with the new hash
        link_file_name, link_file_ext = os.path.splitext(link_file_path)
        link_file_path = f"{link_file_name}_copy{link_file_ext}.lnk"
        count = 1
        while os.path.exists(link_file_path):
            link_file_path = f"{link_file_name}_copy({count}){link_file_ext}.lnk"
            count += 1
        lnk.save(link_file_path)

        # Update the mapping table and hash table
        mapping_table[new_hidden_file_path] = link_file_path[:-4]
        hash_table[new_hash] = new_hidden_file_path

        # Save the updated database
        data["mapping_table"] = mapping_table
        data["hash_table"] = hash_table
        postprocessing(data, aes, pw, enc_mapping_filepath)

        print(f"[+] Successfully created a copy of the hidden file and updated the link file.")
        print(f"    New hidden file: {new_hidden_file_path}")
        print(f"    Updated link file: {link_file_path}")

    except (ValueError, FileNotFoundError) as e:
        print(f"[-] Error: {e}")
    except Exception as e:
        print(f"[-] Unexpected error: {e}")

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--link_file_path", type=str, help="The path of the .lnk shortcut file.")

    args = parser.parse_args()
    if not args.link_file_path:
        print("[-] No link file path provided.")
        print("[*] Usage: copy_link_file.py --link_file_path <link_file_path>")
        input("\n[*] Press Enter to exit...")
        sys.exit(1)
    copy_link_file(args.link_file_path)