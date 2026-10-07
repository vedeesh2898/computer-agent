import os
import subprocess
from datetime import datetime


PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

SCREENSHOT_DIR = os.path.join(PROJECT_DIR, "screenshots")


def capture_screen():
    """
    Capture the current macOS screen and save it as a PNG.

    Returns:
        str: Path to the captured screenshot or an error message.
    """

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    screenshot_path = os.path.join(
        SCREENSHOT_DIR,
        f"screen_{timestamp}.png",
    )

    command = [
        "screencapture",
        "-x",
        "-t",
        "png",
        screenshot_path,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            error = result.stderr.strip()

            if error:
                return f"Screen capture failed: {error}"

            return "Screen capture failed."

        if not os.path.exists(screenshot_path):
            return "Screen capture failed: screenshot was not created."

        return screenshot_path

    except subprocess.TimeoutExpired:
        return "Screen capture failed: command timed out."

    except Exception as e:
        return f"Screen capture failed: {e}"
