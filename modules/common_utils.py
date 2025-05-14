"""
Utils for common operations.

Functions:
- get_dir_path: Retrieves the base directory path for the current environment.
- read_file: Reads the content of a file.
- write_file: Writes data to a file.
- load_json: Loads and parses JSON data from a file.
- ext_to_app_path: Maps file extensions to their corresponding applications.
- move_file: Moves a file from one location to another.
- validate_extension: Validates and sanitizes file extensions.
"""

import os
import sys
import json
import shutil

from filelock import FileLock


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


def load_json(filepath: str) -> dict[str, list | dict | str]:
    """
    Loads JSON data from a file.

    Args:
        filepath (str): Path to the JSON file.

    Returns:
        dict: The parsed JSON data.
    """
    lock = FileLock(f"{filepath}.lock")
    with lock:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)


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
    Moves a file from the source path to the destination path.

    This function attempts to move a file using `os.rename` for efficiency. 
    If `os.rename` fails due to a `PermissionError` or other issues, it falls 
    back to using `shutil.move` to complete the operation.

    Args:
        src_path (str): The source file path.
        dest_path (str): The destination file path.

    Returns:
        bool: True if the file was successfully moved, False otherwise.

    Exceptions:
        - Handles `PermissionError`:
            - If the error code is 5 (Access Denied), it suggests checking permissions.
            - If the file is in use by another process, it advises closing the file.
        - Handles `OSError`:
            - Attempts to use `shutil.move` as a fallback if `os.rename` fails.

    Notes:
        - Ensure the source file exists and the destination path is valid.
        - Proper permissions are required to move the file.
    """
    try:
        os.rename(src_path, dest_path)
        return True
    except PermissionError as e:
        print(f"\n[!] Failed to hide {src_path}: ",end="")
        if e.winerror == 5:
            print(f"Access denied")
            print("[!] Please ensure you have the necessary permissions.\n")
        else:
            print("File is in use by another process.")
            print("[!] Please close the file and try again.\n")
    except OSError:
        try:
            shutil.move(src_path, dest_path)
            return True
        except OSError as e:
            print(e)
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
