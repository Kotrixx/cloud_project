import subprocess


# Function to execute commands with sudo
def run_sudo_command(command, description=""):
    if description:
        print(description)
    sudo_command = f"echo 'ubuntu' | sudo -S {command}"
    process = subprocess.Popen(sudo_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()
    if output:
        print(output)
    if error:
        print(f"Error: {error}")