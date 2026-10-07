import json
import os
import re

import ollama

from tools.files import list_directory, read_file
from tools.terminal import run_command


PROJECT_DIR = os.path.abspath(os.getcwd())
MODEL = "phi3:mini"


# =================================
# TOOL REGISTRY
# =================================

TOOLS = {
    "list_directory": {
        "function": list_directory,
        "description": "List files and folders in the project.",
    },

    "read_file": {
        "function": read_file,
        "description": "Read a text file inside the project.",
    },

    "run_command": {
        "function": run_command,
        "description": "Run an approved terminal command.",
    },
}


# =================================
# FAST INTENT DETECTION
# =================================

def detect_fast_intent(user_request):
    """
    Detect very obvious requests without
    calling the language model.

    Returns a tool request or None.
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

    if any(
        phrase in text
        for phrase in file_phrases
    ):

        return {
            "action": "list_directory"
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
        }


    # ---------------------------------
    # DOCKER VERSION
    # ---------------------------------

    docker_version_phrases = [
        "docker version",
        "docker version installed",
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
        }


    # No obvious intent found.
    return None


# =================================
# VALIDATE TOOL REQUEST
# =================================

def validate_tool_request(tool_request):

    if not isinstance(
        tool_request,
        dict
    ):

        raise ValueError(
            "Tool request must be a JSON object."
        )

    action = tool_request.get(
        "action"
    )

    if not action:

        raise ValueError(
            "Tool request is missing 'action'."
        )

    if action not in TOOLS:

        raise PermissionError(
            f"Tool '{action}' is not registered."
        )


    if action == "read_file":

        filename = tool_request.get(
            "filename"
        )

        if not filename:

            raise ValueError(
                "read_file requires a filename."
            )

        if not isinstance(
            filename,
            str
        ):

            raise ValueError(
                "filename must be a string."
            )


    if action == "run_command":

        command = tool_request.get(
            "command"
        )

        if not command:

            raise ValueError(
                "run_command requires a command."
            )

        if not isinstance(
            command,
            str
        ):

            raise ValueError(
                "command must be a string."
            )

    return True


# =================================
# PARSE MODEL OUTPUT
# =================================

def parse_tool_request(
    model_output
):

    clean_output = model_output.strip()


    if "```json" in clean_output:

        clean_output = clean_output.split(
            "```json",
            1
        )[1]


    if "```" in clean_output:

        clean_output = clean_output.split(
            "```",
            1
        )[0]


    clean_output = clean_output.strip()


    start = clean_output.find(
        "{"
    )

    end = clean_output.rfind(
        "}"
    )


    if start == -1 or end == -1:

        raise ValueError(
            "No JSON tool request found."
        )


    json_text = clean_output[
        start:end + 1
    ]


    # Repair common LLM mistake.
    json_text = re.sub(
        r",\s*}",
        "}",
        json_text
    )

    json_text = re.sub(
        r",\s*]",
        "]",
        json_text
    )


    tool_request = json.loads(
        json_text
    )


    validate_tool_request(
        tool_request
    )


    return tool_request


# =================================
# EXECUTE TOOL
# =================================

def execute_tool(
    tool_request
):

    action = tool_request[
        "action"
    ]

    tool = TOOLS[action]


    print(
        "\nRequested action:",
        action
    )

    print(
        "Tool request validated."
    )

    print(
        "Tool permission granted."
    )


    # ---------------------------------
    # LIST DIRECTORY
    # ---------------------------------

    if action == "list_directory":

        print(
            "Resolved directory:",
            PROJECT_DIR
        )

        return tool["function"](
            PROJECT_DIR
        )


    # ---------------------------------
    # READ FILE
    # ---------------------------------

    if action == "read_file":

        filename = tool_request[
            "filename"
        ]

        requested_path = os.path.abspath(
            os.path.join(
                PROJECT_DIR,
                filename
            )
        )


        print(
            "Requested file:",
            filename
        )

        print(
            "Resolved file:",
            requested_path
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


        if os.path.isdir(
            requested_path
        ):

            raise PermissionError(
                "The requested path is a directory."
            )


        return tool["function"](
            requested_path
        )


    # ---------------------------------
    # RUN COMMAND
    # ---------------------------------

    if action == "run_command":

        command = tool_request[
            "command"
        ]

        print(
            "Requested command:",
            command
        )

        print(
            "Checking command permissions..."
        )

        return tool["function"](
            command
        )


    raise ValueError(
        f"Unknown tool: {action}"
    )


# =================================
# FAST RESPONSE
# =================================

def display_fast_response(
    action,
    result
):

    print(
        "\nTool executed successfully."
    )

    print("\nAgent:")


    if action == "list_directory":

        print(
            "The files and folders in "
            "your project are:"
        )

        if isinstance(
            result,
            list
        ):

            for item in result:

                print(
                    f"- {item}"
                )

        else:

            print(result)

        return


    if action == "read_file":

        max_output = 10000

        if isinstance(
            result,
            str
        ):

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


# =================================
# AI PLANNER
# =================================

def ask_model_for_tool(
    user_request
):

    print(
        "\nAI planning..."
    )


    response = ollama.chat(

        model=MODEL,

        messages=[

            {
                "role": "system",

                "content": """
You are the planning component of a
computer-use AI agent.

Available tools:

1. list_directory
2. read_file
3. run_command

Allowed commands:

- pwd
- ls
- python3 --version
- git status
- git branch
- docker --version
- ollama --version

Return ONLY a JSON tool request.

Examples:

{
    "action": "list_directory"
}

{
    "action": "read_file",
    "filename": "main.py"
}

{
    "action": "run_command",
    "command": "git status"
}

Rules:

- Never use absolute filesystem paths.
- Never invent files.
- Only use allowed commands.
- Return only JSON.
- Do not explain your answer.
- Do not use trailing commas.
""",
            },

            {
                "role": "user",

                "content": user_request,
            },
        ],
    )


    model_output = response[
        "message"
    ]["content"]


    print(
        "\nModel response:"
    )

    print(model_output)


    return parse_tool_request(
        model_output
    )


# =================================
# MAIN
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
        # 1. FAST INTENT DETECTION
        # ---------------------------------

        tool_request = detect_fast_intent(
            user_request
        )


        if tool_request is not None:

            print(
                "\nFast path detected."
            )

        else:

            # ---------------------------------
            # 2. AI PLANNING
            # ---------------------------------

            tool_request = ask_model_for_tool(
                user_request
            )


        # ---------------------------------
        # 3. EXECUTE TOOL
        # ---------------------------------

        action = tool_request[
            "action"
        ]

        result = execute_tool(
            tool_request
        )


        # ---------------------------------
        # 4. DISPLAY RESULT
        # ---------------------------------

        display_fast_response(
            action,
            result
        )


    except json.JSONDecodeError as error:

        print(
            "\nInvalid JSON from model."
        )

        print(
            "Error:",
            error
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