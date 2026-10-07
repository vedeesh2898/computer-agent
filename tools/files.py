import os


def list_directory(path="."):
    """List files and folders in a directory."""
    try:
        return os.listdir(path)
    except Exception as e:
        return f"Error: {e}"


def read_file(path):
    """Read a text file."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Error: {e}"