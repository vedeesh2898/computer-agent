import subprocess


ALLOWED_COMMANDS = {
    "pwd",
    "ls",
    "python3 --version",
    "git status",
    "git branch",
    "docker --version",
    "ollama --version",
}


def run_command(command):
    """Run an approved terminal command."""

    if command not in ALLOWED_COMMANDS:
        return (
            "Command blocked by security policy. "
            f"Allowed commands: {sorted(ALLOWED_COMMANDS)}"
        )

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )

        output = result.stdout.strip()
        error = result.stderr.strip()

        if error:
            return f"Error:\n{error}"

        return output if output else "Command completed successfully."

    except subprocess.TimeoutExpired:
        return "Error: command timed out."

    except Exception as e:
        return f"Error: {e}"