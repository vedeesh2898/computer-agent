import pyautogui


# ==========================================
# MOUSE CONTROL
# ==========================================


def move_mouse(x, y):
    """Move the mouse cursor to the specified screen coordinates."""
    try:
        x = int(x)
        y = int(y)

        if x < 0 or y < 0:
            return "Error: x and y must be non-negative."

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


def double_click_mouse():
    """Double-click the left mouse button at the current cursor position."""
    try:
        pyautogui.doubleClick(interval=0.1)

        return "Mouse double-clicked."

    except Exception as e:
        return f"Error double-clicking mouse: {e}"


def scroll_mouse(amount):
    """
    Scroll vertically.

    Positive values scroll up.
    Negative values scroll down.
    """
    try:
        amount = int(amount)

        if amount == 0:
            return "Error: scroll amount cannot be zero."

        if abs(amount) > 20:
            return "Error: scroll amount is limited to 20."

        pyautogui.scroll(amount)

        direction = "up" if amount > 0 else "down"

        return f"Mouse scrolled {direction} by {abs(amount)}."

    except (TypeError, ValueError):
        return "Error: scroll amount must be a number."

    except Exception as e:
        return f"Error scrolling mouse: {e}"


# ==========================================
# KEYBOARD CONTROL
# ==========================================


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
    """Press one approved keyboard key."""
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
        "pageup",
        "pagedown",
    }

    normalized_key = key.strip().lower()

    if normalized_key not in allowed_keys:
        return (
            "Key blocked by security policy. "
            f"Allowed keys: {sorted(allowed_keys)}"
        )

    try:
        pyautogui.press(normalized_key)

        return f"Key '{normalized_key}' pressed."

    except Exception as e:
        return f"Error pressing key: {e}"


def hotkey(keys):
    """
    Press a safe keyboard shortcut.

    Only explicitly approved shortcut combinations are allowed.
    """
    if not isinstance(keys, list):
        return "Error: keys must be provided as a list."

    if not keys:
        return "Error: at least one key is required."

    normalized_keys = [
        str(key).strip().lower()
        for key in keys
    ]

    allowed_hotkeys = {
        ("command", "a"),
        ("command", "c"),
        ("command", "v"),
        ("command", "x"),
        ("command", "z"),
        ("command", "shift", "z"),
        ("command", "f"),
        ("command", "l"),
        ("command", "n"),
        ("command", "w"),
        ("command", "q"),
        ("command", "tab"),
        ("command", "space"),
        ("control", "a"),
        ("control", "c"),
        ("control", "v"),
        ("control", "x"),
        ("control", "z"),
        ("control", "f"),
    }

    shortcut = tuple(normalized_keys)

    if shortcut not in allowed_hotkeys:
        return (
            "Hotkey blocked by security policy. "
            f"Allowed hotkeys: {sorted(allowed_hotkeys)}"
        )

    try:
        pyautogui.hotkey(*normalized_keys)

        return (
            "Hotkey pressed: "
            + " + ".join(normalized_keys)
            + "."
        )

    except Exception as e:
        return f"Error pressing hotkey: {e}"