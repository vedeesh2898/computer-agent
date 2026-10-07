import pyautogui


def move_mouse(x, y):
    """Move the mouse cursor to the specified screen coordinates."""
    try:
        x = int(x)
        y = int(y)

        pyautogui.moveTo(x, y, duration=0.2)

        return f"Mouse moved to ({x}, {y})."

    except (TypeError, ValueError):
        return "Error: x and y must be numbers."

    except Exception as e:
        return f"Error moving mouse: {e}"


def click_mouse():
    """Click the left mouse button at the current cursor position."""
    try:
        pyautogui.click()
        return "Mouse clicked."

    except Exception as e:
        return f"Error clicking mouse: {e}"


def type_text(text):
    """Type text using the keyboard."""
    if not isinstance(text, str):
        return "Error: text must be a string."

    if len(text) > 500:
        return "Error: text is too long."

    try:
        pyautogui.write(text, interval=0.01)
        return "Text typed successfully."

    except Exception as e:
        return f"Error typing text: {e}"


def press_key(key):
    """Press one keyboard key."""
    if not isinstance(key, str):
        return "Error: key must be a string."

    allowed_keys = {
        "enter",
        "esc",
        "space",
        "tab",
        "backspace",
        "delete",
        "up",
        "down",
        "left",
        "right",
        "home",
        "end",
    }

    if key.lower() not in allowed_keys:
        return (
            "Key blocked by security policy. "
            f"Allowed keys: {sorted(allowed_keys)}"
        )

    try:
        pyautogui.press(key.lower())
        return f"Key '{key.lower()}' pressed."

    except Exception as e:
        return f"Error pressing key: {e}"
