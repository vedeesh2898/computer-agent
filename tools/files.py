import os


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    ".idea",
    ".vscode",
}


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


def find_files(path=".", pattern=""):
    """Find files inside a directory while skipping ignored directories."""

    matches = []

    try:
        for root, directories, files in os.walk(path):

            directories[:] = [
                directory
                for directory in directories
                if directory not in IGNORED_DIRECTORIES
            ]

            for filename in files:

                if not pattern:
                    matches.append(
                        os.path.relpath(
                            os.path.join(root, filename),
                            path,
                        )
                    )

                    continue

                if pattern.lower() in filename.lower():

                    matches.append(
                        os.path.relpath(
                            os.path.join(root, filename),
                            path,
                        )
                    )

        return sorted(matches)

    except Exception as e:

        return f"Error: {e}"