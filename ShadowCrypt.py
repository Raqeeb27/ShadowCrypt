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
import errno
import subprocess
try:
    from modules.common_utils import get_dir_path, hold_console_for_input
except ImportError:
    print("\n[-] Import Error: Ensure that the script is run from the correct directory.\n\nExiting...\n")
    time.sleep(2)
    sys.exit(1)


MAX_ATTEMPTS = 3
WAIT_TIME = 1


def display_banner():
    """
    Displays the ShadowCrypt banner.
    """
    print("\n" + "=" * 75)
    print("\n    _____ __              __                 ______                 __ ")
    print("   / ___// /_  ____ _____/ /___ _      __   / ____/______  ______  / /_")
    print("   \\__ \\/ __ \\/ __ `/ __  / __ \\ | /| / /  / /   / ___/ / / / __ \\/ __/")
    print("  ___/ / / / / /_/ / /_/ / /_/ / |/ |/ /  / /___/ /  / /_/ / /_/ / /_")
    print(" /____/_/ /_/\\__,_/\\__,_/\\____/|__/|__/   \\____/_/   \\__, / .___/\\__/")
    print("                                                    /____/_/\n")
    print("=" * 75)


def should_reinitialize_db():
    """
    Checks if the required .dll files exist in the db directory and if their file sizes are valid.
    Returns True if reinitialization is needed, otherwise False.
    """
    db_dir = os.path.join(get_dir_path(), "db")
    username = os.getlogin()
    required_files = [f"enc_{username}_mapping.dll", "enc_app_path.dll"]

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
        hold_console_for_input()
        sys.exit(1)

    if not should_reinitialize_db():
        try:
            user_input = input("\n[!] Do you want to reinitialize the database?\n**Recommended** - Recover all the hidden files first!\nWarning: This will overwrite the existing databases.\nType 'yes' to continue: ").strip().lower()
            if user_input not in ["yes", "y"]:
                print("\n[-] Reinitialization aborted.")
                hold_console_for_input()
                sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\n\n[!] Keyboard Interrupt!")
            hold_console_for_input()
            sys.exit(1)

    command = [init_db_path, "ShadowCrypt"] if getattr(sys, 'frozen', False) else [sys.executable, init_db_path, "ShadowCrypt"]

    attempts = 0
    while attempts < MAX_ATTEMPTS:
        try:
            subprocess.run(command, check=True)
            break
        except subprocess.CalledProcessError as e:
            if e.returncode == 4294967294:
                hold_console_for_input()
                sys.exit(1)
            attempts += 1
            time.sleep(WAIT_TIME)
            print()
            if attempts >= MAX_ATTEMPTS:
                print("[-] Maximum attempts exceeded.")
                hold_console_for_input()
                sys.exit(1)


def check_init_db():
    """
    Checks if the required .dll files exist in the db directory and reinitializes if needed.
    """
    if should_reinitialize_db():
        print("\n[!] Missing or invalid database files...")
        print("\n[*] Initializing the database...")
        run_init_db()
        return False
    return True


def main():
    """
    Main function to route arguments to the appropriate script.
    """

    display_banner()

    if len(sys.argv) < 2:
        print("\n[-] No module specified.")
        print(f"[*] Usage: ShadowCrypt.{'exe' if getattr(sys, 'frozen', False) else 'py'} <module> [arguments]")
        print("    Modules: hide, link, recover, init")
        if getattr(sys, 'frozen', False):
            print("\nRun below command to initialize the database.")
            print("C:\\\"Program Files (x86)\"\\ShadowCrypt\\dist\\ShadowCrypt.exe init")
        hold_console_for_input()
        sys.exit(1)

    module = sys.argv[1].lower()
    if module == "init":
        print("\n[*] Initializing the database...")
        run_init_db()
        print("\n[*] Database initialized successfully.")
        hold_console_for_input()
        sys.exit(0)

    script_map = {
        "hide": "dist\\hiding.exe" if getattr(sys, 'frozen', False) else "hiding.py",
        "link": "dist\\linker.exe" if getattr(sys, 'frozen', False) else "linker.py",
        "recover": "dist\\recovery.exe" if getattr(sys, 'frozen', False) else "recovery.py",
    }

    if module not in script_map:
        print(f"\n[-] Invalid module: {module}")
        print("[*] Valid modules: hide, link, recover, init")
        hold_console_for_input()
        sys.exit(1)

    isInitialized = check_init_db()
    if module in ["link", "recover"] and not isInitialized:
        print("\n[!] Database just initialized. No hidden files to recover or link.")
        print("\n[*] Run the command below to hide files.")
        print(f"[*] Usage: ShadowCrypt.{'exe' if getattr(sys, 'frozen', False) else 'py'} hide --files <file1> <file2> ...")
        hold_console_for_input()
        sys.exit(1)

    script_path = os.path.join(get_dir_path(), script_map[module])
    if not os.path.exists(script_path):
        print(f"[-] Script not found: {script_path}")
        hold_console_for_input()
        sys.exit(1)

    if getattr(sys, 'frozen', False):
        command = [script_path] + sys.argv[2:]
    else:
        command = [sys.executable, script_path] + sys.argv[2:]

    try:
        subprocess.run(command, check=True)
    except OSError as e:
        winerror = getattr(e, "winerror", None)
        if e.errno == errno.EPERM or winerror == 225:
            print("\n[!] It looks like a security program is preventing this application from running.")
            print("\n[*] To fix this, please try the following steps:")
            print("    1. Reinstall ShadowCrypt.")
            print("    2. Add the installation directory (e.g., 'C:\\Program Files (x86)\\ShadowCrypt') to your antivirus or security software's exclusion list.")
            print("    3. Restart your computer and try again.\n\nExiting...\n")
        else:
            print(f"\n[!] OS Error occurred: {e}")
        hold_console_for_input()
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] An unexpected error occurred: {e}")
        hold_console_for_input()
        sys.exit(1)

    return module


if __name__ == "__main__":
    module = main()
    if not module == "link":
        hold_console_for_input()
