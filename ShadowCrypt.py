"""
ShadowCrypt - Entry Point Script

This script serves as the main entry point for ShadowCrypt, allowing users to execute
the following modules via command-line arguments:

    - hide:    Hide files using the hiding module.
    - link:    Link hashed filenames using the linker module.
    - recover: Recover files using the recovery module.
    - init:    (Re)initialize the database.

The script automatically checks for required database files and reinitializes them if missing
or invalid.

Usage Examples:
    python ShadowCrypt.py hide --files <file1 file2 ...>
    python ShadowCrypt.py link --hash <hashed_filename>
    python ShadowCrypt.py recover --all
    python ShadowCrypt.py init
"""

import os
import sys
import time
import subprocess
from modules.common_utils import get_dir_path


MAX_ATTEMPTS = 3
WAIT_TIME = 1


def should_reinitialize_db():
    """
    Checks if the required .dll files exist in the db directory and if their file sizes are valid.
    Returns True if reinitialization is needed, otherwise False.
    """
    db_dir = os.path.join(get_dir_path(), "db")
    required_files = ["enc_mapping.dll", "app_path.dll"]

    for file in required_files:
        file_path = os.path.join(db_dir, file)
        if not os.path.exists(file_path):
            return True
        if os.path.getsize(file_path) == 0:
            return True
    return False


def run_init_db():
    """
    Runs the init_db script to reinitialize the database.
    """
    init_db_filename = "init_db.exe" if getattr(sys, 'frozen', False) else "init_db.py"
    file_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
    init_db_path = os.path.join(os.path.dirname(file_path), init_db_filename)

    if not os.path.exists(init_db_path):
        print(f"[-] `{init_db_filename}` not found at: {init_db_path}")
        input("\n[*] Press Enter to exit...")
        sys.exit(1)

    if not should_reinitialize_db():
        try:
            user_input = input("\n[!] Do you want to reinitialize the database?\nWarning: This will overwrite the existing databases.\nType 'yes' to continue: ").strip().lower()
            print()
            if user_input not in ["yes", "y"]:
                print("\n[-] User aborted the reinitialization.")
                input("\n[*] Press Enter to exit...")
                sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\n[!] Keyboard Interrupt!")
            input("\n[*] Press Enter to exit...")
            sys.exit(1)

    command = [init_db_path] if getattr(sys, 'frozen', False) else [sys.executable, init_db_path]

    attempts = 0
    while attempts < MAX_ATTEMPTS:
        try:
            subprocess.run(command, check=True)
            break
        except subprocess.CalledProcessError as e:
            if e.returncode == 4294967294:
                input("\n[*] Press Enter to exit...")
                sys.exit(1)
            attempts += 1
            time.sleep(WAIT_TIME)
            print()
            if attempts >= MAX_ATTEMPTS:
                print("[-] Maximum attempts exceeded.")
                input("\n[*] Press Enter to exit...")
                sys.exit(1)


def check_init_db():
    """
    Checks if the required .dll files exist in the db directory and reinitializes if needed.
    """
    if should_reinitialize_db():
        print("\n[!] Missing or invalid database files...")
        print("\n[*] Initializing the database...")
        run_init_db()


def main():
    """
    Main function to route arguments to the appropriate script.
    """
    if len(sys.argv) < 2:
        print("[-] No module specified.")
        print(f"[*] Usage: ShadowCrypt.exe <module> [arguments]") if getattr(sys, 'frozen', False) else print("[*] Usage: ShadowCrypt.py <module> [arguments]")
        print("    Modules: hide, link, recover, init")
        if getattr(sys, 'frozen', False):
            print("\nRun below command to initialize the database.")
            print("C:\\\"Program Files (x86)\"\\ShadowCrypt\\dist\\ShadowCrypt.exe init")
        input("\n[*] Press Enter to exit...")
        sys.exit(1)

    module = sys.argv[1].lower()
    if module == "init":
        print("\n[*] Initializing the database...")
        run_init_db()
        print("[*] Database initialized successfully.")
        input("\n[*] Press Enter to exit...")
        sys.exit(0)

    script_map = {
        "hide": "dist\\hiding.exe" if getattr(sys, 'frozen', False) else "hiding.py",
        "link": "dist\\linker.exe" if getattr(sys, 'frozen', False) else "linker.py",
        "recover": "dist\\recovery.exe" if getattr(sys, 'frozen', False) else "recovery.py",
    }

    if module not in script_map:
        print(f"[-] Invalid module: {module}")
        print("[*] Valid modules: hide, link, recover, init")
        input("\n[*] Press Enter to exit...")
        sys.exit(1)

    check_init_db()

    script_path = os.path.join(get_dir_path(), script_map[module])
    if not os.path.exists(script_path):
        print(f"[-] Script not found: {script_path}")
        input("\n[*] Press Enter to exit...")
        sys.exit(1)

    if getattr(sys, 'frozen', False):
        command = [script_path] + sys.argv[2:]
    else:
        command = [sys.executable, script_path] + sys.argv[2:]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(1)


if __name__ == "__main__":
    main()
    input("\n[*] Press Enter to exit...")
