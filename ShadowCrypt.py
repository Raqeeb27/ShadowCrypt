"""
This script acts as an entry point to execute hide, link, or recover modules
based on the command-line arguments provided. It checks if the script is running in
a frozen state (e.g., using PyInstaller) and adjusts the script paths accordingly.

Usage:
    python ShadowCrypt.py hide --files <file1 file2 ...>   # Executes hiding.py
    python ShadowCrypt.py link --hash <hashed_filename>    # Executes linker.py
    python ShadowCrypt.py recover --all                    # Executes recovery.py
"""

import os
import sys
import subprocess
from modules.common_utils import get_dir_path

def main():
    """
    Main function to route arguments to the appropriate script.
    """
    if len(sys.argv) < 2:
        print("[-] No module specified.")
        print("[*] Usage: ShadowCrypt.py <module> [arguments]")
        print("    Modules: hide, link, recover")
        sys.exit(1)

    module = sys.argv[1].lower()
    script_map = {
        "hide": "dist\\hiding.exe" if getattr(sys, 'frozen', False) else "hiding.py",
        "link": "dist\\linker.exe" if getattr(sys, 'frozen', False) else "linker.py",
        "recover": "dist\\recovery.exe" if getattr(sys, 'frozen', False) else "recovery.py",
    }

    if module not in script_map:
        print(f"[-] Invalid module: {module}")
        print("[*] Valid modules: hide, link, recover")
        sys.exit(1)

    script_path = os.path.join(get_dir_path(), script_map[module])
    if not os.path.exists(script_path):
        print(f"[-] Script not found: {script_path}")
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
