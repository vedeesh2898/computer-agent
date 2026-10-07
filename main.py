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
    type_text,
    press_key,
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
        "description": "Capture the current Mac screen as an image.",
    },

    "move_mouse": {
        "function": move_mouse,
        "description": "Move the mouse cursor to screen coordinates.",
    },

    "click_mouse": {
        "function": click_mouse,
        "description": "Click the left mouse button at the current cursor position.",
    },

    "type_text": {
        "function": type_text,
        "description": "Type text using the keyboard.",
    },

    "press_key": {
        "function": press_key,
        "description": "Press one approved keyboard key.",
    },
}


# =================================
# INPUT SECURITY
# =================================

def validate_user_request_safety(user_request):
    """
    Reject obviously dangerous path requests before
    they reach the LLM planner or any filesystem tool.
    """

    if not isinstance(user_request, str):
        raise ValueError(
            "User request must be a string."
        )

    text = user_request.strip()

    # ---------------------------------
    # PARENT-DIRECTORY TRAVERSAL
    # ---------------------------------

    if re.search(
        r"(^|[\s\"'])\.\.(?:[\\/]|$)",
        text,
    ):
        raise PermissionError(
            "Path traversal is not allowed."
        )

    # ---------------------------------
    # ABSOLUTE UNIX PATHS
    # ---------------------------------

    if re.search(
        r"(^|[\s\"'])/(?:[^/\s\"']+/?)+",
        text,
    ):
        raise PermissionError(
            "Absolute paths are not allowed."
        )

    # ---------------------------------
    # WINDOWS DRIVE PATHS
    # ---------------------------------

    if re.search(
        r"(^|[\s\"'])[a-zA-Z]:[\\/]",
        text,
    ):
        raise PermissionError(
            "Absolute paths are not allowed."
        )

    # ---------------------------------
    # UNC / NETWORK PATHS
    # ---------------------------------

    if re.search(
        r"(^|[\s\"'])\\\\",
        text,
    ):
        raise PermissionError(
            "Network paths are not allowed."
        )

    return True


# =================================
# FAST INTENT DETECTION
# =================================

def detect_fast_intent(user_request):
    """Detect obvious requests without using the LLM."""

    text = user_request.lower().strip()

    # ---------------------------------
    # SCREENSHOT
    # ---------------------------------

    screenshot_phrases = [
        "take a screenshot",
        "capture the screen",
        "capture my screen",
        "take screenshot",
        "screenshot",
        "show me the screen",
        "look at my screen",
    ]

    if any(
        phrase in text
        for phrase in screenshot_phrases
    ):
        return {
            "action": "capture_screen",
            "needs_reasoning": False,
        }

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

    if any(
        phrase in text
        for phrase in file_phrases
    ):
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

    if any(
        phrase in text
        for phrase in python_file_phrases
    ):
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

    if any(
        phrase in text
        for phrase in javascript_file_phrases
    ):
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

    if any(
        phrase in text
        for phrase in json_file_phrases
    ):
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
        match = re.search(
            pattern,
            text,
        )

        if match:
            filename = match.group(1)

            return {
                "action": "find_files",
                "pattern": filename,
                "needs_reasoning": False,
            }

    # ---------------------------------
    # READ FILE BY NAME
    # ---------------------------------

    read_patterns = [
        r"read\s+([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)",
        r"open\s+([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)",
        r"show\s+me\s+([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)",
    ]

    for pattern in read_patterns:
        match = re.search(
            pattern,
            text,
        )

        if match:
            filename = match.group(1)

            return {
                "action": "read_file",
                "filename": filename,
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

    if any(
        phrase in text
        for phrase in python_version_phrases
    ):
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

    if any(
        phrase in text
        for phrase in git_status_phrases
    ):
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

    if any(
        phrase in text
        for phrase in git_branch_phrases
    ):
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

    if any(
        phrase in text
        for phrase in docker_version_phrases
    ):
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

    if any(
        phrase in text
        for phrase in ollama_version_phrases
    ):
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

    if any(
        phrase in text
        for phrase in directory_phrases
    ):
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
    # READ FILE VALIDATION
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
    # FIND FILES VALIDATION
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
    # COMMAND VALIDATION
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
    # MOUSE VALIDATION
    # ---------------------------------

    if action == "move_mouse":

        x = tool_request.get("x")
        y = tool_request.get("y")

        if isinstance(x, bool) or not isinstance(
            x,
            (int, float),
        ):
            raise ValueError(
                "move_mouse requires numeric x."
            )

        if isinstance(y, bool) or not isinstance(
            y,
            (int, float),
        ):
            raise ValueError(
                "move_mouse requires numeric y."
            )

        if x < 0 or y < 0:
            raise PermissionError(
                "Mouse coordinates cannot be negative."
            )

    # ---------------------------------
    # TYPE TEXT VALIDATION
    # ---------------------------------

    if action == "type_text":

        text = tool_request.get("text")

        if not isinstance(text, str):
            raise ValueError(
                "type_text requires a string."
            )

        if len(text) > 500:
            raise PermissionError(
                "type_text is limited to 500 characters."
            )

    # ---------------------------------
    # KEY VALIDATION
    # ---------------------------------

    if action == "press_key":

        key = tool_request.get("key")

        if not isinstance(key, str):
            raise ValueError(
                "press_key requires a string key."
            )

    # ---------------------------------
    # CLICK VALIDATION
    # ---------------------------------

    if action == "click_mouse":
        # click_mouse has no user-controlled arguments.
        pass

    # ---------------------------------
    # SCREEN CAPTURE VALIDATION
    # ---------------------------------

    if action == "capture_screen":
        # capture_screen has no user-controlled arguments.
        pass

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

        print(
            "Tool permission granted."
        )

        print(
            "Resolved directory:",
            PROJECT_DIR,
        )

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

        print(
            "Tool permission granted."
        )

        pattern = tool_request.get(
            "pattern",
            "",
        )

        print(
            "Search pattern:",
            pattern,
        )

        print(
            "Search directory:",
            PROJECT_DIR,
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

        print(
            "Tool permission granted."
        )

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
    # CAPTURE SCREEN
    # ---------------------------------

    if action == "capture_screen":

        print(
            "Tool permission granted."
        )

        print(
            "Capturing current Mac screen..."
        )

        result = tool["function"]()

        if isinstance(result, str) and result.endswith(
            ".png"
        ):
            print(
                "Tool executed successfully."
            )

        return result

    # ---------------------------------
    # MOVE MOUSE
    # ---------------------------------

    if action == "move_mouse":

        x = tool_request["x"]
        y = tool_request["y"]

        print(
            "Tool permission granted."
        )

        print(
            f"Moving mouse to ({x}, {y})..."
        )

        result = tool["function"](
            x,
            y,
        )

        print(
            "Tool executed successfully."
        )

        return result

    # ---------------------------------
    # CLICK MOUSE
    # ---------------------------------

    if action == "click_mouse":

        print(
            "Tool permission granted."
        )

        print(
            "Clicking current mouse position..."
        )

        result = tool["function"]()

        print(
            "Tool executed successfully."
        )

        return result

    # ---------------------------------
    # TYPE TEXT
    # ---------------------------------

    if action == "type_text":

        text = tool_request["text"]

        print(
            "Tool permission granted."
        )

        print(
            "Typing requested text..."
        )

        result = tool["function"](
            text
        )

        print(
            "Tool executed successfully."
        )

        return result

    # ---------------------------------
    # PRESS KEY
    # ---------------------------------

    if action == "press_key":

        key = tool_request["key"]

        print(
            "Tool permission granted."
        )

        print(
            f"Pressing key: {key}"
        )

        result = tool["function"](
            key
        )

        if isinstance(result, str) and result.startswith(
            "Key blocked by security policy."
        ):
            print(
                "Tool execution blocked."
            )
        else:
            print(
                "Tool executed successfully."
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

    The model is only responsible for planning.
    Final responses are generated deterministically.
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

REAL PROJECT FILES:

{file_list}

You may ONLY choose a filename from the REAL PROJECT FILES list.

Tool formats:

{{
  "action": "list_directory"
}}

{{
  "action": "find_files",
  "pattern": ".py"
}}

{{
  "action": "read_file",
  "filename": "main.py"
}}

{{
  "action": "run_command",
  "command": "git status"
}}

{{
  "action": "capture_screen"
}}

{{
  "action": "move_mouse",
  "x": 500,
  "y": 500
}}

{{
  "action": "click_mouse"
}}

{{
  "action": "type_text",
  "text": "Hello"
}}

{{
  "action": "press_key",
  "key": "enter"
}}

Allowed commands:

- pwd
- ls
- python3 --version
- git status
- git branch
- docker --version
- ollama --version

IMPORTANT:

- Return EXACTLY ONE JSON object.
- Do not return explanations.
- Do not return Markdown.
- Never invent filenames.
- Never use absolute paths.
- Never use /output paths.
- Never use ../ paths.
- read_file filenames MUST come from REAL PROJECT FILES.
- Only use allowed commands.
- For computer actions, only use the fields shown in the tool formats.
- Never invent tool names.
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

    # ---------------------------------
    # LIST DIRECTORY
    # ---------------------------------

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

    # ---------------------------------
    # FIND FILES
    # ---------------------------------

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

    # ---------------------------------
    # READ FILE
    # ---------------------------------

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

    # ---------------------------------
    # RUN COMMAND
    # ---------------------------------

    if action == "run_command":

        print(result)

        return

    # ---------------------------------
    # SCREEN CAPTURE
    # ---------------------------------

    if action == "capture_screen":

        print(
            "Screen captured successfully."
        )

        print(
            "Screenshot:",
            result,
        )

        return

    # ---------------------------------
    # COMPUTER CONTROL
    # ---------------------------------

    if action in {
        "move_mouse",
        "click_mouse",
        "type_text",
        "press_key",
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

    # ---------------------------------
    # GIT STATUS EXPLANATION
    # ---------------------------------

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

            # ---------------------------------
            # SECURITY VALIDATION FOR FAST PATH
            # ---------------------------------

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
            print(f"- {filename}")

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