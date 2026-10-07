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
    """Detect obvious requests without using the LLM."""

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

        needs_reasoning = any(
            phrase in text
            for phrase in [
                "tell me if",
                "tell me whether",
                "what does",
                "what does this mean",
                "explain",
                "analyze",
                "analyse",
                "need to commit",
                "needs committing",
                "uncommitted",
            ]
        )

        return {
            "action": "run_command",
            "command": "git status",
            "needs_reasoning": needs_reasoning,
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

Return ONLY one JSON object.

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

- Choose the single best tool for the request.
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
# AI FINAL RESPONSE
# =================================

def reason_about_result(
    user_request,
    action,
    result
):

    print(
        "\nAI reasoning..."
    )

    observation = str(
        result
    )

    max_observation = 12000

    if len(observation) > max_observation:

        observation = (
            observation[:max_observation]
            + "\n[Observation truncated]"
        )

    prompt = f"""
The user asked:

{user_request}

The computer agent executed:

{action}

The ACTUAL result was:

{observation}

Interpret this result for the user.

Use ONLY the actual result.

Do not invent information.

Do not request another tool.

Return a concise natural-language answer.
"""

    response = ollama.chat(

        model=MODEL,

        messages=[

            {
                "role": "system",

                "content": """
You are the reasoning component of
a computer-use AI agent.

The computer observation is authoritative.

Never invent computer state.

Explain what the result means for
the user's original request.

Return only natural language.
""",
            },

            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response[
        "message"
    ]["content"]


# =================================
# DISPLAY SIMPLE RESPONSE
# =================================

def display_simple_response(
    action,
    result
):

    print(
        "\nTool executed successfully."
    )

    print(
        "\nAgent:"
    )

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
        # 1. FAST INTENT DETECTION
        # ---------------------------------

        fast_request = detect_fast_intent(
            user_request
        )

        if fast_request is not None:

            print(
                "\nFast path detected."
            )

            result = execute_tool(
                fast_request
            )

            action = fast_request[
                "action"
            ]

            needs_reasoning = (
                fast_request.get(
                    "needs_reasoning",
                    False
                )
            )

            if not needs_reasoning:

                display_simple_response(
                    action,
                    result
                )

                return

            # One reasoning call for
            # requests that need interpretation.

            final_response = reason_about_result(
                user_request,
                action,
                result
            )

            print(
                "\nAgent:"
            )

            print(
                final_response
            )

            return

        # ---------------------------------
        # 2. ONE AI PLANNING CALL
        # ---------------------------------

        tool_request = ask_model_for_tool(
            user_request
        )

        # ---------------------------------
        # 3. EXECUTE TOOL
        # ---------------------------------

        result = execute_tool(
            tool_request
        )

        # ---------------------------------
        # 4. ONE AI REASONING CALL
        # ---------------------------------

        final_response = reason_about_result(
            user_request,
            tool_request["action"],
            result
        )

        print(
            "\nAgent:"
        )

        print(
            final_response
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