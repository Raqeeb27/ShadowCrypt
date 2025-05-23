"""
Common utility functions for file and path operations.

Functions:
- get_dir_path: Retrieves the base directory path of the current script or executable.
- read_file: Reads the content of a text file with file locking.
- write_file: Writes data to a file with file locking.
- check_db_files: Checks for the existence of the encrypted database files.
- ext_to_app_path: Maps a file extension to the corresponding application path.
- move_file: Atomically moves a file from src_path to dest_path on Windows.
- process_filename_for_extension: Validates and sanitizes the file extension of a given file path.
- hold_console_for_input: Waits for user input before exiting.
"""

import os
import sys
import time

from filelock import FileLock

import ctypes
import ctypes.wintypes as wintypes


MOVEFILE_REPLACE_EXISTING = 0x1
MOVEFILE_COPY_ALLOWED = 0x2

MoveFileExW = ctypes.windll.kernel32.MoveFileExW
MoveFileExW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
MoveFileExW.restype = wintypes.BOOL

GetLastError = ctypes.windll.kernel32.GetLastError


def get_dir_path() -> str:
    """
    Retrieves the base directory path of the current script or executable.

    Returns:
        str: The base directory path.
    """
    if getattr(sys, "frozen", False):  # When running as a bundled executable
        file_path = sys.executable
        file_name = os.path.basename(file_path)
        return file_path.split(f"\\dist\\{file_name}", maxsplit=1)[0]
    else:  # When running as a script
        file_path = os.path.abspath(__file__)
        return os.path.dirname(os.path.dirname(file_path))


def read_file(filepath: str) -> str:
    """
    Reads the content of a text file.

    Args:
        filepath (str): Path to the file.

    Returns:
        str: The content of the file.
    """
    if not os.path.exists(filepath):
        print(f"[!] File not found: {filepath}")
        sys.exit(1)
    lock = FileLock(f"{filepath}.lock")
    with lock:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()


def write_file(filepath: str, data: str) -> None:
    """
    Writes data to a file.

    Args:
        filepath (str): Path to the file.
        data (str): Data to write to the file.

    Returns:
        None
    """
    lock = FileLock(f"{filepath}.lock")
    with lock:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)


def check_db_files() -> tuple[str, str]:
    """
    Checks for the existence of the encrypted database files.

    Returns:
        tuple[str, str]: Paths to the encrypted mapping and application path files.
    """
    dir_path = get_dir_path()
    username = os.getlogin()

    enc_mapping_filepath = os.path.join(dir_path, "db", f"enc_{username}_mapping.dll")
    enc_app_path_filepath = os.path.join(dir_path, "db", "enc_app_path.dll")

    if not os.path.exists(enc_mapping_filepath) or not os.path.exists(enc_app_path_filepath):
        print("\n[-] Encrypted database files not found. Please reinitialize the database or ensure that the script is run from the correct directory.")
        hold_console_for_input()
        sys.exit(1)

    return enc_mapping_filepath, enc_app_path_filepath


def ext_to_app_path(ext: str, app_path_db: dict[str, dict[str, list | str]]) -> str:
    """
    Maps a file extension to the corresponding application path.

    Args:
        ext (str): The file extension (e.g., "txt", "jpg").
        app_path_dict (dict): A dictionary mapping application names
                              to their properties, including supported extensions.

    Returns:
        str: The path to the application associated with the given extension, 
             or an empty string if not found.
    """
    for info in app_path_db.values():
        if ext in info.get("ext", []):
            return info.get("path", "")
    return ""


def move_file(src_path: str, dest_path: str) -> bool:
    """
    Atomically moves a file from src_path to dest_path on Windows using MoveFileExW.

    Attempts to move the file, replacing the destination if it exists. Handles common errors such as
    permission issues and file-in-use scenarios, providing informative messages for each case.
    This function attempts to minimize time-of-check to time-of-use (TOCTOU) vulnerabilities and does not fall back
    to copy/delete operations.

    Args:
        src_path (str): The full path to the source file.
        dest_path (str): The full path to the destination file.

    Returns:
        bool: True if the file was moved successfully, False otherwise.
    """

    success = MoveFileExW(src_path, dest_path, MOVEFILE_REPLACE_EXISTING | MOVEFILE_COPY_ALLOWED)
    if success:
        return True

    error_code = GetLastError()

    if error_code == 5:
        print(f"\n[!] Access Denied for {src_path}: Check file/folder permissions or run as administrator.")
    elif error_code == 32:
        print(f"\n[!] File is in use by another process {src_path}. Close the file and try again.")
    else:
        print(f"\n[!] Failed with error code {error_code}\n")

    return False


def process_filename_for_extension(file_path: str) -> str | None:
    """
    Validates and sanitizes the file extension of a given file path.

    This function checks if the provided file path has a valid file extension. 
    If the extension is missing or invalid, it logs an error message and returns None. 
    Otherwise, it returns the sanitized file path with the valid extension.

    Args:
        file_path (str): The path to the file to validate.

    Returns:
        str | None: The sanitized file path with the valid extension, or None if the 
                    extension is invalid or missing.
    """
    directory = os.path.dirname(file_path)
    file_path = os.path.join(directory, os.path.basename(file_path).strip())
    ext = os.path.splitext(file_path)[1].split(" ")[0]
    if not ext or ext.strip() == ".":
        print(f"[!] Error in filename {file_path}: Invalid or Missing file extension.")
        return None
    else:
        end_of_filename = file_path.rfind(ext) + len(ext)
        return file_path[:end_of_filename]


def hold_console_for_input() -> None:
    """
    Waits for user input before exiting.

    This function prompts the user to press Enter before the program exits.
    Useful for allowing users to read messages before the console window closes.
    """
    try:
        input("\n[*] Press Enter to exit...")
    except (KeyboardInterrupt, EOFError):
        print("\n\n[!] Keyboard Interrupt\n")
        time.sleep(0.75)
        sys.exit(1)
