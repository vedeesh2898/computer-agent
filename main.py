import json
import os
import re

import ollama

from tools.files import (
    find_files,
    list_directory,
    read_file,
)
from tools.terminal import run_command
from tools.screen import capture_screen
from tools.input import (
    move_mouse,
    click_mouse,
    double_click_mouse,
    scroll_mouse,
    type_text,
    press_key,
    hotkey,
)
from tools.apps import (
    open_app,
    close_app,
    focus_app,
)


# =================================
# CONFIGURATION
# =================================

PROJECT_DIR = os.path.abspath(os.getcwd())

MODEL = "qwen3:1.7b"


# =================================
# TOOL REGISTRY
# =================================

TOOLS = {
    "list_directory": {
        "function": list_directory,
        "description": "List files and folders in the project.",
    },
    "find_files": {
        "function": find_files,
        "description": "Find files inside the project.",
    },
    "read_file": {
        "function": read_file,
        "description": "Read a text file inside the project.",
    },
    "run_command": {
        "function": run_command,
        "description": "Run an approved terminal command.",
    },
    "capture_screen": {
        "function": capture_screen,
        "description": "Capture the current macOS screen.",
    },
    "move_mouse": {
        "function": move_mouse,
        "description": "Move the mouse to screen coordinates.",
    },
    "click_mouse": {
        "function": click_mouse,
        "description": "Click the left mouse button.",
    },

    "double_click_mouse": {
        "function": double_click_mouse,
        "description": "Double-click the left mouse button.",
    },

    "scroll_mouse": {
        "function": scroll_mouse,
        "description": "Scroll vertically.",
    },
    "type_text": {
        "function": type_text,
        "description": "Type text using the keyboard.",
    },
    "press_key": {
        "function": press_key,
        "description": "Press an approved keyboard key.",
    },

    "hotkey": {
        "function": hotkey,
        "description": "Press an approved keyboard shortcut.",
    },
    "open_app": {
        "function": open_app,
        "description": "Open an approved macOS application.",
    },
    "close_app": {
        "function": close_app,
        "description": "Close an approved macOS application.",
    },
    "focus_app": {
        "function": focus_app,
        "description": "Bring an approved macOS application to the foreground.",
    },
}


# =================================
# INPUT SECURITY
# =================================

def validate_user_request_safety(user_request):
    """
    Reject obviously dangerous path requests before
    they reach the LLM planner.
    """

    if not isinstance(user_request, str):
        raise ValueError("User request must be a string.")

    text = user_request.strip()

    if re.search(r"(^|[\s\"'])\.\.(?:[\\/]|$)", text):
        raise PermissionError(
            "Path traversal is not allowed."
        )

    if re.search(r"(^|[\s\"'])/(?:[^/\s\"']+/?)+", text):
        raise PermissionError(
            "Absolute paths are not allowed."
        )

    if re.search(r"(^|[\s\"'])[a-zA-Z]:[\\/]", text):
        raise PermissionError(
            "Absolute paths are not allowed."
        )

    if re.search(r"(^|[\s\"'])\\\\", text):
        raise PermissionError(
            "Network paths are not allowed."
        )

    return True


# =================================
# FAST INTENT DETECTION
# =================================

def detect_fast_intent(user_request):
    """
    Detect obvious requests without using the LLM.
    """

    text = user_request.lower().strip()

    # ---------------------------------
    # LIST FILES
    # ---------------------------------

    file_phrases = [
        "show me the files",
        "show the files",
        "list the files",
        "list files",
        "show files",
        "what files are in",
        "what files do i have",
        "show my files",
    ]

    if any(phrase in text for phrase in file_phrases):
        return {
            "action": "list_directory",
            "needs_reasoning": False,
        }

    # ---------------------------------
    # FIND PYTHON FILES
    # ---------------------------------

    python_file_phrases = [
        "python files",
        "python file",
        "files with .py",
        ".py files",
        "files ending in .py",
    ]

    if any(phrase in text for phrase in python_file_phrases):
        return {
            "action": "find_files",
            "pattern": ".py",
            "needs_reasoning": False,
        }

    # ---------------------------------
    # FIND JAVASCRIPT FILES
    # ---------------------------------

    javascript_file_phrases = [
        "javascript files",
        "javascript file",
        "js files",
        ".js files",
        "files with .js",
        "files ending in .js",
    ]

    if any(phrase in text for phrase in javascript_file_phrases):
        return {
            "action": "find_files",
            "pattern": ".js",
            "needs_reasoning": False,
        }

    # ---------------------------------
    # FIND JSON FILES
    # ---------------------------------

    json_file_phrases = [
        "json files",
        "json file",
        ".json files",
        "files with .json",
    ]

    if any(phrase in text for phrase in json_file_phrases):
        return {
            "action": "find_files",
            "pattern": ".json",
            "needs_reasoning": False,
        }

    # ---------------------------------
    # FIND FILE BY NAME
    # ---------------------------------

    find_patterns = [
        r"find\s+([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)",
        r"locate\s+([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)",
        r"where\s+is\s+([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)",
    ]

    for pattern in find_patterns:
        match = re.search(pattern, text)

        if match:
            return {
                "action": "find_files",
                "pattern": match.group(1),
                "needs_reasoning": False,
            }

    # ---------------------------------
    # READ FILE BY NAME
    # ---------------------------------

    read_patterns = [
        r"read\s+([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)",
        r"show\s+me\s+([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)",
    ]

    for pattern in read_patterns:
        match = re.search(pattern, text)

        if match:
            return {
                "action": "read_file",
                "filename": match.group(1),
                "needs_reasoning": False,
            }

    # ---------------------------------
    # SCREENSHOT
    # ---------------------------------

    screenshot_phrases = [
        "take a screenshot",
        "take screenshot",
        "capture the screen",
        "capture my screen",
        "capture screen",
        "screenshot",
        "show me the screen",
        "look at my screen",
    ]

    if any(phrase in text for phrase in screenshot_phrases):
        return {
            "action": "capture_screen",
            "needs_reasoning": False,
        }

    # ---------------------------------
    # DOUBLE CLICK
    # ---------------------------------

    double_click_phrases = [
        "double click",
        "double-click",
        "double click here",
        "double-click here",
    ]

    if any(
        phrase in text
        for phrase in double_click_phrases
    ):
        return {
            "action": "double_click_mouse",
            "needs_reasoning": False,
        }

    # ---------------------------------
    # SCROLL DOWN
    # ---------------------------------

    scroll_down_phrases = [
        "scroll down",
        "scroll downward",
        "scroll down the page",
    ]

    if any(
        phrase in text
        for phrase in scroll_down_phrases
    ):
        return {
            "action": "scroll_mouse",
            "amount": -3,
            "needs_reasoning": False,
        }

    # ---------------------------------
    # SCROLL UP
    # ---------------------------------

    scroll_up_phrases = [
        "scroll up",
        "scroll upward",
        "scroll up the page",
    ]

    if any(
        phrase in text
        for phrase in scroll_up_phrases
    ):
        return {
            "action": "scroll_mouse",
            "amount": 3,
            "needs_reasoning": False,
        }

    # ---------------------------------
    # SAFE HOTKEYS
    # ---------------------------------

    hotkey_phrases = {
        "select all": ["command", "a"],
        "copy": ["command", "c"],
        "paste": ["command", "v"],
        "cut": ["command", "x"],
        "undo": ["command", "z"],
        "find": ["command", "f"],
        "open new window": ["command", "n"],
        "close window": ["command", "w"],
        "switch app": ["command", "tab"],
    }

    for phrase, keys in hotkey_phrases.items():
        if text == phrase or text == f"press {phrase}":
            return {
                "action": "hotkey",
                "keys": keys,
                "needs_reasoning": False,
            }


    # ---------------------------------
    # OPEN APPLICATION
    # ---------------------------------

    open_app_match = re.search(
        r"^(?:please\s+)?open\s+(.+?)(?:\s+app)?$",
        text,
    )

    if open_app_match:
        app_name = open_app_match.group(1).strip()

        if "." not in app_name:
            return {
                "action": "open_app",
                "app_name": app_name,
                "needs_reasoning": False,
            }

    # ---------------------------------
    # CLOSE APPLICATION
    # ---------------------------------

    close_app_match = re.search(
        r"^(?:please\s+)?close\s+(.+?)(?:\s+app)?$",
        text,
    )

    if close_app_match:
        app_name = close_app_match.group(1).strip()

        if "." not in app_name:
            return {
                "action": "close_app",
                "app_name": app_name,
                "needs_reasoning": False,
            }

    # ---------------------------------
    # FOCUS APPLICATION
    # ---------------------------------

    focus_app_match = re.search(
        r"^(?:please\s+)?focus\s+(?:on\s+)?(.+?)(?:\s+app)?$",
        text,
    )

    if focus_app_match:
        app_name = focus_app_match.group(1).strip()

        return {
            "action": "focus_app",
            "app_name": app_name,
            "needs_reasoning": False,
        }

    # ---------------------------------
    # PYTHON VERSION
    # ---------------------------------

    python_version_phrases = [
        "python version",
        "my python version",
        "what version of python",
        "which python version",
        "check python version",
    ]

    if any(phrase in text for phrase in python_version_phrases):
        return {
            "action": "run_command",
            "command": "python3 --version",
            "needs_reasoning": False,
        }

    # ---------------------------------
    # GIT STATUS
    # ---------------------------------

    git_status_phrases = [
        "git status",
        "check git status",
        "my git status",
        "git status of my project",
    ]

    if any(phrase in text for phrase in git_status_phrases):
        return {
            "action": "run_command",
            "command": "git status",
            "needs_reasoning": False,
        }

    # ---------------------------------
    # GIT BRANCH
    # ---------------------------------

    git_branch_phrases = [
        "git branch",
        "current git branch",
        "which git branch",
        "what branch am i on",
        "what branch are we on",
    ]

    if any(phrase in text for phrase in git_branch_phrases):
        return {
            "action": "run_command",
            "command": "git branch",
            "needs_reasoning": False,
        }

    # ---------------------------------
    # DOCKER VERSION
    # ---------------------------------

    docker_version_phrases = [
        "docker version",
        "what version of docker",
        "check docker version",
    ]

    if any(phrase in text for phrase in docker_version_phrases):
        return {
            "action": "run_command",
            "command": "docker --version",
            "needs_reasoning": False,
        }

    # ---------------------------------
    # OLLAMA VERSION
    # ---------------------------------

    ollama_version_phrases = [
        "ollama version",
        "what version of ollama",
        "check ollama version",
    ]

    if any(phrase in text for phrase in ollama_version_phrases):
        return {
            "action": "run_command",
            "command": "ollama --version",
            "needs_reasoning": False,
        }

    # ---------------------------------
    # CURRENT DIRECTORY
    # ---------------------------------

    directory_phrases = [
        "current directory",
        "where am i",
        "what directory am i in",
        "show current directory",
        "show my current directory",
    ]

    if any(phrase in text for phrase in directory_phrases):
        return {
            "action": "run_command",
            "command": "pwd",
            "needs_reasoning": False,
        }

    return None


# =================================
# PROJECT FILE DISCOVERY
# =================================

def discover_project_files():
    """Return real project files for validation and planning."""

    files = find_files(
        PROJECT_DIR,
        "",
    )

    if not isinstance(files, list):
        raise RuntimeError(
            f"Could not discover project files: {files}"
        )

    return files


# =================================
# VALIDATE TOOL REQUEST
# =================================

def validate_tool_request(
    tool_request,
    available_files=None,
):
    """Validate a tool request before execution."""

    if not isinstance(tool_request, dict):
        raise ValueError(
            "Tool request must be a JSON object."
        )

    action = tool_request.get("action")

    if not action:
        raise ValueError(
            "Tool request is missing 'action'."
        )

    if action not in TOOLS:
        raise PermissionError(
            f"Tool '{action}' is not registered."
        )

    # ---------------------------------
    # READ FILE
    # ---------------------------------

    if action == "read_file":
        filename = tool_request.get("filename")

        if not filename:
            raise ValueError(
                "read_file requires a filename."
            )

        if not isinstance(filename, str):
            raise ValueError(
                "filename must be a string."
            )

        if os.path.isabs(filename):
            raise PermissionError(
                "read_file does not allow absolute paths."
            )

        normalized_filename = os.path.normpath(
            filename
        )

        if (
            normalized_filename == ".."
            or normalized_filename.startswith(
                ".." + os.sep
            )
        ):
            raise PermissionError(
                "read_file does not allow "
                "parent-directory traversal."
            )

        if available_files is not None:
            if normalized_filename not in available_files:
                raise PermissionError(
                    "The selected file does not exist "
                    "in the discovered project files."
                )

    # ---------------------------------
    # FIND FILES
    # ---------------------------------

    if action == "find_files":
        pattern = tool_request.get(
            "pattern",
            "",
        )

        if not isinstance(pattern, str):
            raise ValueError(
                "pattern must be a string."
            )

    # ---------------------------------
    # COMMAND
    # ---------------------------------

    if action == "run_command":
        command = tool_request.get("command")

        if not command:
            raise ValueError(
                "run_command requires a command."
            )

        if not isinstance(command, str):
            raise ValueError(
                "command must be a string."
            )

    # ---------------------------------
    # MOUSE
    # ---------------------------------

    if action == "move_mouse":
        x = tool_request.get("x")
        y = tool_request.get("y")

        if isinstance(x, bool) or isinstance(y, bool):
            raise ValueError(
                "Mouse coordinates must be numbers."
            )

        try:
            x = int(x)
            y = int(y)
        except (TypeError, ValueError):
            raise ValueError(
                "Mouse coordinates must be numbers."
            )

        if x < 0 or y < 0:
            raise PermissionError(
                "Mouse coordinates cannot be negative."
            )

    # ---------------------------------
    # TYPE TEXT
    # ---------------------------------

    if action == "type_text":
        text = tool_request.get("text")

        if not isinstance(text, str):
            raise ValueError(
                "type_text requires a string."
            )

        if len(text) > 500:
            raise PermissionError(
                "Typed text is limited to 500 characters."
            )

    # ---------------------------------
    # PRESS KEY
    # ---------------------------------

    if action == "press_key":
        key = tool_request.get("key")

        if not isinstance(key, str):
            raise ValueError(
                "press_key requires a key string."
            )

    # ---------------------------------
    # DOUBLE CLICK
    # ---------------------------------

    if action == "double_click_mouse":
        return True

    # ---------------------------------
    # SCROLL
    # ---------------------------------

    if action == "scroll_mouse":
        amount = tool_request.get("amount")

        if isinstance(amount, bool):
            raise ValueError(
                "Scroll amount must be a number."
            )

        try:
            amount = int(amount)
        except (TypeError, ValueError):
            raise ValueError(
                "Scroll amount must be a number."
            )

        if amount == 0:
            raise ValueError(
                "Scroll amount cannot be zero."
            )

        if abs(amount) > 20:
            raise PermissionError(
                "Scroll amount is limited to 20."
            )

    # ---------------------------------
    # HOTKEY
    # ---------------------------------

    if action == "hotkey":
        keys = tool_request.get("keys")

        if not isinstance(keys, list):
            raise ValueError(
                "hotkey requires a list of keys."
            )

        if not keys:
            raise ValueError(
                "hotkey requires at least one key."
            )

        if len(keys) > 4:
            raise PermissionError(
                "Hotkeys are limited to 4 keys."
            )

        if not all(
            isinstance(key, str)
            for key in keys
        ):
            raise ValueError(
                "Hotkey keys must be strings."
            )


    # ---------------------------------
    # APPLICATION CONTROL
    # ---------------------------------

    if action in {
        "open_app",
        "close_app",
        "focus_app",
    }:
        app_name = tool_request.get("app_name")

        if not isinstance(app_name, str):
            raise ValueError(
                f"{action} requires an app_name string."
            )

        if not app_name.strip():
            raise ValueError(
                "Application name cannot be empty."
            )

    return True


# =================================
# EXTRACT FIRST JSON OBJECT
# =================================

def extract_first_json_object(text):
    """Extract the first complete JSON object."""

    start = text.find("{")

    if start == -1:
        raise ValueError(
            "No JSON object found in model output."
        )

    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(text)):
        character = text[index]

        if in_string:
            if escape:
                escape = False

            elif character == "\\":
                escape = True

            elif character == '"':
                in_string = False

            continue

        if character == '"':
            in_string = True

        elif character == "{":
            depth += 1

        elif character == "}":
            depth -= 1

            if depth == 0:
                return text[start:index + 1]

    raise ValueError(
        "Incomplete JSON object in model output."
    )


# =================================
# PARSE MODEL OUTPUT
# =================================

def parse_tool_request(
    model_output,
    available_files=None,
):
    """Parse and validate the model's JSON tool request."""

    clean_output = model_output.strip()

    if "```json" in clean_output:
        clean_output = clean_output.split(
            "```json",
            1,
        )[1]

    json_text = extract_first_json_object(
        clean_output
    )

    json_text = re.sub(
        r",\s*}",
        "}",
        json_text,
    )

    json_text = re.sub(
        r",\s*]",
        "]",
        json_text,
    )

    tool_request = json.loads(json_text)

    validate_tool_request(
        tool_request,
        available_files,
    )

    return tool_request


# =================================
# EXECUTE TOOL
# =================================

def execute_tool(
    tool_request,
    available_files=None,
):
    """Validate and execute a tool request."""

    validate_tool_request(
        tool_request,
        available_files,
    )

    action = tool_request["action"]
    tool = TOOLS[action]

    print(
        "\nRequested action:",
        action,
    )

    print(
        "Tool request validated."
    )

    # ---------------------------------
    # LIST DIRECTORY
    # ---------------------------------

    if action == "list_directory":
        print("Tool permission granted.")

        result = tool["function"](
            PROJECT_DIR
        )

        print(
            "Tool executed successfully."
        )

        return result

    # ---------------------------------
    # FIND FILES
    # ---------------------------------

    if action == "find_files":
        print("Tool permission granted.")

        pattern = tool_request.get(
            "pattern",
            "",
        )

        result = tool["function"](
            PROJECT_DIR,
            pattern,
        )

        print(
            "Tool executed successfully."
        )

        return result

    # ---------------------------------
    # READ FILE
    # ---------------------------------

    if action == "read_file":
        print("Tool permission granted.")

        filename = tool_request["filename"]

        requested_path = os.path.abspath(
            os.path.join(
                PROJECT_DIR,
                filename,
            )
        )

        print(
            "Requested file:",
            filename,
        )

        print(
            "Resolved file:",
            requested_path,
        )

        project_prefix = (
            PROJECT_DIR + os.sep
        )

        if not requested_path.startswith(
            project_prefix
        ):
            raise PermissionError(
                "The agent cannot access "
                "files outside the project."
            )

        if os.path.isdir(requested_path):
            raise PermissionError(
                "The requested path is a directory."
            )

        result = tool["function"](
            requested_path
        )

        print(
            "Tool executed successfully."
        )

        return result

    # ---------------------------------
    # RUN COMMAND
    # ---------------------------------

    if action == "run_command":
        command = tool_request["command"]

        print(
            "Requested command:",
            command,
        )

        print(
            "Checking command permissions..."
        )

        result = tool["function"](
            command
        )

        if (
            isinstance(result, str)
            and result.startswith(
                "Command blocked by security policy."
            )
        ):
            print(
                "Tool execution blocked."
            )
        else:
            print(
                "Tool permission granted."
            )
            print(
                "Tool executed successfully."
            )

        return result

    # ---------------------------------
    # SCREEN CAPTURE
    # ---------------------------------

    if action == "capture_screen":
        print("Checking screen capture permission...")

        result = tool["function"]()

        print(
            "Screen capture executed."
        )

        return result

    # ---------------------------------
    # MOVE MOUSE
    # ---------------------------------

    if action == "move_mouse":
        x = tool_request["x"]
        y = tool_request["y"]

        print(
            f"Requested mouse position: ({x}, {y})"
        )

        print(
            "Mouse control permission granted."
        )

        result = tool["function"](
            x,
            y,
        )

        return result

    # ---------------------------------
    # CLICK MOUSE
    # ---------------------------------

    if action == "click_mouse":
        print(
            "Mouse click permission granted."
        )

        result = tool["function"]()

        return result

    # ---------------------------------
    # DOUBLE CLICK
    # ---------------------------------

    if action == "double_click_mouse":
        print(
            "Mouse double-click permission granted."
        )

        result = tool["function"]()

        return result

    # ---------------------------------
    # SCROLL MOUSE
    # ---------------------------------

    if action == "scroll_mouse":
        amount = tool_request["amount"]

        print(
            f"Requested scroll amount: {amount}"
        )

        print(
            "Mouse scroll permission granted."
        )

        result = tool["function"](
            amount
        )

        return result

    # ---------------------------------
    # HOTKEY
    # ---------------------------------

    if action == "hotkey":
        keys = tool_request["keys"]

        print(
            "Keyboard shortcut permission checking..."
        )

        result = tool["function"](
            keys
        )

        return result

    # ---------------------------------
    # TYPE TEXT
    # ---------------------------------

    if action == "type_text":
        text = tool_request["text"]

        print(
            "Keyboard typing permission granted."
        )

        result = tool["function"](
            text
        )

        return result

    # ---------------------------------
    # PRESS KEY
    # ---------------------------------

    if action == "press_key":
        key = tool_request["key"]

        print(
            "Keyboard key permission checking..."
        )

        result = tool["function"](
            key
        )

        return result

    # ---------------------------------
    # OPEN APPLICATION
    # ---------------------------------

    if action == "open_app":
        app_name = tool_request["app_name"]

        print(
            "Requested application:",
            app_name,
        )

        print(
            "Application permission checking..."
        )

        result = tool["function"](
            app_name
        )

        if (
            isinstance(result, str)
            and result.startswith(
                "Application blocked by security policy."
            )
        ):
            print(
                "Application execution blocked."
            )
        else:
            print(
                "Application permission granted."
            )

        return result

    # ---------------------------------
    # CLOSE APPLICATION
    # ---------------------------------

    if action == "close_app":
        app_name = tool_request["app_name"]

        print(
            "Requested application:",
            app_name,
        )

        print(
            "Application close permission checking..."
        )

        result = tool["function"](
            app_name
        )

        if (
            isinstance(result, str)
            and result.startswith(
                "Application blocked by security policy."
            )
        ):
            print(
                "Application execution blocked."
            )
        else:
            print(
                "Application close permission granted."
            )

        return result

    # ---------------------------------
    # FOCUS APPLICATION
    # ---------------------------------

    if action == "focus_app":
        app_name = tool_request["app_name"]

        print(
            "Requested application:",
            app_name,
        )

        print(
            "Application focus permission checking..."
        )

        result = tool["function"](
            app_name
        )

        if (
            isinstance(result, str)
            and result.startswith(
                "Application blocked by security policy."
            )
        ):
            print(
                "Application execution blocked."
            )
        else:
            print(
                "Application focus permission granted."
            )

        return result

    raise ValueError(
        f"Unknown tool: {action}"
    )


# =================================
# AI PLANNER
# =================================

def ask_model_for_tool(
    user_request,
    available_files,
):
    """
    Use Qwen3 once to select the appropriate tool.
    """

    print("\nAI planning...")

    file_list = "\n".join(
        f"- {filename}"
        for filename in available_files
    )

    system_prompt = f"""
You are the planning component of a computer-use AI agent.

Select exactly ONE tool for the user's request.

Available tools:

1. list_directory
2. find_files
3. read_file
4. run_command
5. capture_screen
6. move_mouse
7. click_mouse
8. type_text
9. press_key
10. open_app
11. close_app
12. focus_app
13. double_click_mouse
14. scroll_mouse
15. hotkey

REAL PROJECT FILES:

{file_list}

Tool formats:

{{"action":"list_directory"}}

{{"action":"find_files","pattern":".py"}}

{{"action":"read_file","filename":"main.py"}}

{{"action":"run_command","command":"git status"}}

{{"action":"capture_screen"}}

{{"action":"move_mouse","x":500,"y":500}}

{{"action":"click_mouse"}}

{{"action":"type_text","text":"Hello"}}

{{"action":"press_key","key":"enter"}}

{{"action":"open_app","app_name":"Safari"}}

{{"action":"close_app","app_name":"Safari"}}

{{"action":"focus_app","app_name":"Safari"}}

{{"action":"double_click_mouse"}}

{{"action":"scroll_mouse","amount":-3}}

{{"action":"hotkey","keys":["command","a"]}}

Allowed terminal commands:

- pwd
- ls
- python3 --version
- git status
- git branch
- docker --version
- ollama --version

Approved macOS applications include:

- Safari
- TextEdit
- Calculator
- Terminal
- Finder
- Notes
- System Settings

IMPORTANT RULES:

- Return EXACTLY ONE JSON object.
- Do not return explanations.
- Do not return Markdown.
- Never invent filenames.
- Never use absolute paths.
- Never use ../ paths.
- read_file filenames MUST come from REAL PROJECT FILES.
- Only use allowed terminal commands.
- Only request approved applications.
- Do not create shell commands for application control.
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_request,
            },
        ],
        options={
            "temperature": 0,
            "num_predict": 120,
        },
        think=False,
    )

    model_output = response["message"]["content"]

    print("\nModel response:")
    print(model_output)

    return parse_tool_request(
        model_output,
        available_files,
    )


# =================================
# DISPLAY RESPONSE
# =================================

def display_response(
    user_request,
    action,
    result,
):
    """Display the result of a tool operation."""

    print("\nAgent:")

    if action == "list_directory":
        print(
            "The files and folders in "
            "your project are:"
        )

        if isinstance(result, list):
            for item in result:
                print(f"- {item}")
        else:
            print(result)

        return

    if action == "find_files":
        print("Matching files:")

        if isinstance(result, list):
            if not result:
                print("No matching files found.")
            else:
                for item in result:
                    print(f"- {item}")
        else:
            print(result)

        return

    if action == "read_file":
        if isinstance(result, str):
            max_output = 10000

            if len(result) > max_output:
                print(
                    result[:max_output]
                )
                print(
                    "\n[Output truncated]"
                )
            else:
                print(result)
        else:
            print(result)

        return

    if action == "run_command":
        print(result)
        return

    if action == "capture_screen":
        print(result)
        return

    if action in {
        "move_mouse",
        "click_mouse",
        "double_click_mouse",
        "scroll_mouse",
        "type_text",
        "press_key",
        "hotkey",
        "open_app",
        "close_app",
        "focus_app",
    }:
        print(result)
        return


# =================================
# SMART RESPONSE HELPERS
# =================================

def explain_result(
    user_request,
    tool_request,
    result,
):
    """
    Add deterministic explanations for common
    agent questions without another LLM call.
    """

    action = tool_request["action"]

    if (
        action == "run_command"
        and tool_request.get("command")
        == "git status"
    ):
        result_text = str(result)

        if "working tree clean" in result_text:
            print(
                "\nYour Git working tree is clean. "
                "There are no changes that need committing."
            )
            return True

        if (
            "modified:" in result_text
            or "Changes not staged" in result_text
            or "Untracked files" in result_text
        ):
            print(
                "\nYou have changes in the working tree "
                "that have not been committed yet."
            )
            return True

    return False


# =================================
# MAIN AGENT
# =================================

def main():

    user_request = input(
        "You: "
    )

    print(
        "\nProcessing..."
    )

    try:

        # ---------------------------------
        # INPUT SECURITY GATE
        # ---------------------------------

        validate_user_request_safety(
            user_request
        )

        # ---------------------------------
        # FAST INTENT DETECTION
        # ---------------------------------

        fast_request = detect_fast_intent(
            user_request
        )

        if fast_request is not None:

            print(
                "\nFast path detected."
            )

            available_files = None

            if fast_request["action"] == "read_file":
                print(
                    "\nChecking requested file "
                    "against project files..."
                )

                available_files = (
                    discover_project_files()
                )

            result = execute_tool(
                fast_request,
                available_files,
            )

            action = fast_request["action"]

            display_response(
                user_request,
                action,
                result,
            )

            return

        # ---------------------------------
        # DISCOVER REAL PROJECT FILES
        # ---------------------------------

        available_files = (
            discover_project_files()
        )

        print(
            "\nDiscovered project files:"
        )

        for filename in available_files:
            print(
                f"- {filename}"
            )

        # ---------------------------------
        # AI PLANNING
        # ---------------------------------

        tool_request = ask_model_for_tool(
            user_request,
            available_files,
        )

        # ---------------------------------
        # TOOL EXECUTION
        # ---------------------------------

        result = execute_tool(
            tool_request,
            available_files,
        )

        # ---------------------------------
        # DETERMINISTIC RESPONSE
        # ---------------------------------

        if not explain_result(
            user_request,
            tool_request,
            result,
        ):
            display_response(
                user_request,
                tool_request["action"],
                result,
            )

    except json.JSONDecodeError as error:

        print(
            "\nInvalid JSON from model."
        )

        print(
            "Error:",
            error,
        )

    except PermissionError as error:

        print(
            "\nPermission denied."
        )

        print(error)

    except ValueError as error:

        print(
            "\nInvalid request."
        )

        print(error)

    except Exception as error:

        print(
            "\nAgent error."
        )

        print(error)


# =================================
# ENTRY POINT
# =================================

if __name__ == "__main__":
    main()
