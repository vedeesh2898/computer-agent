import subprocess


# Applications the agent is allowed to control.
ALLOWED_APPS = {
    "safari": "Safari",
    "textedit": "TextEdit",
    "calculator": "Calculator",
    "terminal": "Terminal",
    "finder": "Finder",
    "notes": "Notes",
    "system settings": "System Settings",
}


def open_app(app_name):
    """Open an approved macOS application."""
    if not isinstance(app_name, str):
        return "Error: application name must be a string."

    key = app_name.strip().lower()

    if key not in ALLOWED_APPS:
        return (
            "Application blocked by security policy. "
            f"Allowed applications: {sorted(ALLOWED_APPS.keys())}"
        )

    application = ALLOWED_APPS[key]

    try:
        result = subprocess.run(
            ["open", "-a", application],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            error = result.stderr.strip()

            if error:
                return f"Error opening {application}: {error}"

            return f"Error opening {application}."

        return f"{application} opened successfully."

    except subprocess.TimeoutExpired:
        return "Error: opening application timed out."

    except Exception as e:
        return f"Error opening application: {e}"


def close_app(app_name):
    """Close an approved macOS application."""
    if not isinstance(app_name, str):
        return "Error: application name must be a string."

    key = app_name.strip().lower()

    if key not in ALLOWED_APPS:
        return (
            "Application blocked by security policy. "
            f"Allowed applications: {sorted(ALLOWED_APPS.keys())}"
        )

    application = ALLOWED_APPS[key]

    try:
        result = subprocess.run(
            ["osascript", "-e", f'tell application "{application}" to quit'],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            error = result.stderr.strip()

            if error:
                return f"Error closing {application}: {error}"

            return f"Error closing {application}."

        return f"{application} closed successfully."

    except subprocess.TimeoutExpired:
        return "Error: closing application timed out."

    except Exception as e:
        return f"Error closing application: {e}"


def focus_app(app_name):
    """Bring an approved macOS application to the foreground."""
    if not isinstance(app_name, str):
        return "Error: application name must be a string."

    key = app_name.strip().lower()

    if key not in ALLOWED_APPS:
        return (
            "Application blocked by security policy. "
            f"Allowed applications: {sorted(ALLOWED_APPS.keys())}"
        )

    application = ALLOWED_APPS[key]

    try:
        result = subprocess.run(
            ["osascript", "-e", f'tell application "{application}" to activate'],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            error = result.stderr.strip()

            if error:
                return f"Error focusing {application}: {error}"

            return f"Error focusing {application}."

        return f"{application} focused successfully."

    except subprocess.TimeoutExpired:
        return "Error: focusing application timed out."

    except Exception as e:
        return f"Error focusing application: {e}"
