import os
import subprocess
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

def remove_ansi_escape_sequences(text):
    ansi_escape_pattern = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape_pattern.sub('', text)

def python(STORAGE_PATH: str, code: str, py_packages: str = "", sys_packages: str = "", uuid_value: str = ""):
    # Use the existing storage path
    workdir = os.path.join(STORAGE_PATH, "interpreter", uuid_value)
    fileLocation = os.path.abspath(workdir)

    # Get environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    replicate_api_token = os.getenv("REPLICATE_API_TOKEN")

    dockerCommand = f"docker run -v {fileLocation}:/runtime:rw --rm --name interpreter-{uuid_value}"

    if openai_api_key:
        dockerCommand += f" -e OPENAI_API_KEY={openai_api_key}"
    if replicate_api_token:
        dockerCommand += f" -e REPLICATE_API_TOKEN={replicate_api_token}"

    dockerCommand += " interpreter"

    fullCommand = dockerCommand.split(" ")

    if py_packages:
        # Create new virtual env and install packages
        fullCommand += ["sh", "-c", f"python3 -m venv /runtime/env && . /runtime/env/bin/activate && pip install {py_packages} && ipython -c \"{code}\""]
    elif sys_packages:
        # Install system packages and run code
        fullCommand += ["sh", "-c", f"apt-get update && apt-get install -y {sys_packages} && ipython -c \"{code}\""]
    else:
        # Just run the code
        fullCommand += ["ipython", "-c", code]

    # Initialize stdout and stderr
    stdout, stderr = "", ""

    try:
        # Execute the command
        output = subprocess.Popen(fullCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = output.communicate(timeout=30)  # 30 seconds timeout
    except subprocess.TimeoutExpired:
        # Kill the Docker container if the command times out
        subprocess.call(["docker", "kill", f"interpreter-{uuid_value}"])
        stderr = str("Process killed due to timeout. Python interpreter runs for a maximum of 30 seconds.").encode("utf-8")
    finally:
        stdout = remove_ansi_escape_sequences(stdout.decode("utf-8") if stdout else "")
        stderr = remove_ansi_escape_sequences(stderr.decode("utf-8") if stderr else "")
        files_list = os.listdir(fileLocation)

    try:
        subprocess.call(["docker", "kill", f"interpreter-{uuid_value}"])
    except:
        pass

    return {"stdout": stdout, "stderr": stderr, "files": files_list}
