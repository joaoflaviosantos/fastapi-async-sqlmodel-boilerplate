# Built-in Dependencies
import subprocess
import tempfile
import os
import re

# Function to print colored text
def print_color(color, text):
    colors = {"RED": "\033[1;31m", "GREEN": "\033[0;32m", "YELLOW": "\033[1;33m", "BLUE": "\033[1;34m", "RESET": "\033[0m"}
    print(f"{colors[color]}{text}{colors['RESET']}")

# Function to read user input with color
def read_color(color, prompt):
    return input(f"{color}{prompt}\033[0m")

# Function to display help menu
def display_help():
    print_color("BLUE", "Select an option:\n")
    print("1 - Local Development Mode")
    print("2 - Production Deployment Setup")
    print("3 - Exit")

# Check if Python 3.11 and Poetry are installed
def check_dependencies():
    python_installed = subprocess.run(["python3.11", "-V"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    poetry_installed = subprocess.run(["poetry", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    return python_installed, poetry_installed

# Step 0: Check dependencies
python_installed, poetry_installed = check_dependencies()
if not python_installed or not poetry_installed:
    print_color("RED", "\nError: Python 3.11 and Poetry are required. Please install them before running this setup.")
    exit(1)

# Print boilerplate name and description
print_color("YELLOW", "#########################################################################################################################")
print_color("YELLOW", "####################################### FastAPI Async SQLModel Boilerplate (Setup) ######################################")
print_color("YELLOW", "#########################################################################################################################\n")

print_color("GREEN", "Supercharge your FastAPI development. A backend for perfectionists with deadlines and lovers of asynchronous programming.\n")

# Display help menu initially
display_help()

# Step 0: Ask user for action
choice = read_color("\033[1;37m", "\nEnter the number corresponding to your choice: ")

# Process user choice
if choice == "1":
    print_color("RED", "\n-> You chose Local Development Mode...\n")

    # Step 1.1: Navigate to the project directory
    os.chdir("backend/")

    # Step 1.2: Install dependencies
    subprocess.run(["poetry", "install"])

    # Step 1.3: Check if .env file exists before copying
    if not os.path.isfile(".env"):
        subprocess.run(["cp", ".env.example", ".env"])
        print_color("GREEN", "\nCopied '.env.example' to '.env'.")
    else:
        print_color("YELLOW", "\n'.env' file already exists. Skipping copy step.")

    # Step 1.4: Check if SECRET_KEY is empty before generating
    secret_key_generated = False
    with open(".env", "r") as f:
        lines = f.readlines()

    with open(".env", "w") as f:
        for line in lines:
            if line.startswith("SECRET_KEY="):
                current_secret_key = line.split("=")[1].strip('" \n')
                if not current_secret_key:
                    secret_key = subprocess.run(["poetry", "run", "python", "-c", "from fastapi import FastAPI; import secrets; print(secrets.token_urlsafe(32))"], capture_output=True, text=True).stdout.strip()
                    f.write(f"SECRET_KEY={secret_key}\n")
                    secret_key_generated = True
                else:
                    f.write(line)
            else:
                f.write(line)

    # Inform the user about generating the SECRET_KEY
    if secret_key_generated:
        print_color("GREEN", "\nGenerated and set a secure secret key in '.env'.\n")
    else:
        print_color("YELLOW", "\n'SECRET_KEY' in '.env' is already set. Skipping generation step.\n")

    # Step 1.5: Inform the user to modify other environment variables in ".env"
    print_color("BLUE", "Please modify other environment variables in 'backend/.env' as needed.\n")

    # Step 1.6: Check if all required environment variables are defined
    # Define a list of dictionaries for database environment variables
    database_env_vars = [
        {"name": "POSTGRES_USER", "type": "string"},
        {"name": "POSTGRES_PASSWORD", "type": "string"},
        {"name": "POSTGRES_SERVER", "type": "string"},
        {"name": "POSTGRES_PORT", "type": "numeric"},
        {"name": "POSTGRES_DB", "type": "string"}
    ]

    # Define a list of dictionaries for Redis for caching environment variables
    redis_env_vars = [
        {"name": "REDIS_CACHE_HOST", "type": "string"},
        {"name": "REDIS_CACHE_PORT", "type": "numeric"},
        {"name": "REDIS_CACHE_DB", "type": "numeric"},
        {"name": "REDIS_CACHE_USERNAME", "type": "string"},
        {"name": "REDIS_CACHE_PASSWORD", "type": "string"}
    ]

    # Define a list of dictionaries for the first admin user environment variable
    first_admin_user_env_vars = [
        {"name": "ADMIN_NAME", "type": "string"},
        {"name": "ADMIN_EMAIL", "type": "email"},
        {"name": "ADMIN_USERNAME", "type": "string"},
        {"name": "ADMIN_PASSWORD", "type": "string"}
    ]

    # Define a list of dictionaries for the default tier environment variable
    default_tier_env_vars = [
        {"name": "TIER_NAME_DEFAULT", "type": "string"}
    ]

    # Combine all sets of environment variables into a single list
    all_env_vars = [database_env_vars, redis_env_vars, first_admin_user_env_vars, default_tier_env_vars]

    # Loop through all environment variables to check if any variable is missing
    for env_vars in all_env_vars:
        any_var_missing = False
        
        # Check if any environment variable is missing
        for var in env_vars:
            with open(".env", "r") as f:
                lines = f.readlines()
            
            # Check if the environment variable is defined in the .env file
            var_defined = any(line.startswith(f"{var['name']}=") and line.split("=")[1].strip('" \n') for line in lines)
            
            if not var_defined:
                any_var_missing = True
                break  # Stop checking if any variable is missing
        
        # If any variable is missing, prompt the user for input
        if any_var_missing:
            print("\nSome environment variables are not defined. Please provide the following information:")
            
            # Loop through all environment variables to ask for user input
            for var in env_vars:
                with open(".env", "r") as f:
                    lines = f.readlines()

                with open(".env", "w") as f:
                    for line in lines:
                        if line.startswith(f"{var['name']}="):
                            current_value = line.split("=")[1].strip('" \n')
                            if current_value:
                                # Value exists, ask the user if they want to keep it
                                keep_value = read_color("\033[1;37m", f"Do you want to keep the value '{current_value}' for {var['name']}? (y/n): ").lower()
                                if keep_value in {"n", "no"}:
                                    # User wants to change the value, ask for new value
                                    new_value = read_color("\033[1;37m", f"Enter the new value for {var['name']}: ")
                                    if var["type"] == "string":
                                        f.write(f"{var['name']}=\"{new_value}\"\n")
                                    else:
                                        f.write(f"{var['name']}={new_value}\n")
                                else:
                                    f.write(line)
                            else:
                                # Value does not exist, ask the user for new value
                                if var["type"] == "email":
                                    # Special case for email, ensure it's a valid email address
                                    # While loop to ensure a valid email address is provided
                                    new_value = read_color("\033[1;37m", f"Enter a valid email address for {var['name']}: ")
                                    while not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_value):
                                        print("Invalid email address. Please enter a valid email.")
                                        new_value = read_color("\033[1;37m", f"Enter a valid email address for {var['name']}: ")
                                    f.write(f"{var['name']}=\"{new_value}\"\n")
                                else:
                                    new_value = read_color("\033[1;37m", f"Enter the value for {var['name']}: ")
                                    if var["type"] == "string":
                                        f.write(f"{var['name']}=\"{new_value}\"\n")
                                    else:
                                        f.write(f"{var['name']}={new_value}\n")
                        else:
                            f.write(line)

    # Step 1.7: Run Alembic migrations
    print_color("GREEN", "\nRunning Alembic migrations...\n")
    subprocess.run(["poetry", "run", "alembic", "upgrade", "head"])

    # Step 1.8: Display a success message for Local Development Mode
    print_color("RED", "\n-> Setup complete for Local Development Mode...\n")

    # Step 1.9: Ask the user if they want to perform additional actions
    print_color("BLUE", "Do you want to perform any additional actions?\n")
    print("1 - Start the FastAPI server")
    print("2 - Start the ARQ worker")
    print("3 - Run unit tests")
    print("4 - Run linting and formatting checks")
    print("5 - Commit and Push Changes")
    print("6 - Exit")

    # Step 1.10: Ask the user for additional action choice
    additional_action = read_color("\033[1;37m", "\nEnter the number corresponding to your choice: ")

    # Process user's additional action choice
    if additional_action == "1":
        print_color("RED", "\n-> Starting the FastAPI server...\n")
        # Step 1.1.1: Start the FastAPI server
        subprocess.run(["poetry", "run", "uvicorn", "src.main:app", "--reload"])
        print_color("RED", "\n-> Stopping the FastAPI server...\n")
    elif additional_action == "2":
        print_color("RED", "\n-> Running the ARQ worker...\n")
        # Step 1.2.1: Start the ARQ worker
        subprocess.run(["poetry", "run", "arq", "src.worker.WorkerSettings"])
        print_color("RED", "\n-> Finished running the ARQ worker...\n")
    elif additional_action == "3":
        print_color("RED", "\n-> Running unit tests...\n")
        # Step 1.3.1: Run unit tests
        subprocess.run(["poetry", "run", "python", "-m", "pytest", "-vv", "./tests"])
        print_color("RED", "\n-> Finished running unit tests...\n")
    elif additional_action == "4":
        print_color("RED", "\n-> Running linting and formatting checks...\n")
        # Step 1.4.1: Run linting and formatting checks
        subprocess.run(["poetry", "run", "python", "-m", "black", "."])
        print_color("RED", "\n-> Finished running linting and formatting checks...\n")
    elif additional_action == "5":
        print_color("RED", "\n-> Committing and pushing changes...\n")

        # Step 1.5.1: Return to the root directory
        os.chdir("..")

        # Step 1.5.2: Ask the user which files they want to include in the commit
        include_all_files = read_color("\033[1;37m", "Do you want to include all files in this commit? (y/n): ").lower()

        if include_all_files in {"y", "yes"}:
            # Include all files
            subprocess.run(["git", "add", "."])
        else:
            # Ask the user to enter the files to include in the commit
            files_to_commit = read_color("\033[1;37m", "Please enter the files to include in the commit (space-separated): ")
            # Include the specified files
            subprocess.run(["git", "add"] + files_to_commit.split())

        # Step 1.5.3: Clean the variables at the beginning
        branch = ""
        message = ""
        description = ""

        # Step 1.5.4: Get the current branch name
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()

        # Step 1.5.5: Check if BRANCH is not empty
        if not branch:
            print_color("RED", "\n-> Error: Unable to determine the current branch name. Please try again.\n")
            exit(1)

        # Step 1.5.6: Loop until MESSAGE is not empty
        while not message:
            # Get the commit message from the user
            message = read_color("\033[1;37m", "Please enter the commit message: ")

            # Remove double quotes from the 'MESSAGE' variable
            message = message.replace('"', '')

            # Check if MESSAGE is not empty
            if not message:
                print_color("RED", "\n-> Error: Commit message cannot be empty. Please try again.\n")

        # Step 1.5.7: Ask the user if they want to include an additional commit description (optional)
        include_description = read_color("\033[1;37m", "Do you want to include an additional commit description? (y/n): ").lower()

        # Check if the user wants to include an additional description
        if include_description in {"y", "yes"}:
            # Use a temporary file to capture the commit description
            with tempfile.NamedTemporaryFile(suffix=".txt") as tmp_file:
                # Open the temporary file in the appropriate text editor based on the operating system
                if os.name == 'nt':  # Windows
                    subprocess.call(['notepad.exe', tmp_file.name])
                else:  # Linux
                    editor = os.environ.get('EDITOR', 'nano')
                    subprocess.call([editor, tmp_file.name])
                # Read the content of the temporary file
                with open(tmp_file.name, "r") as f:
                    description = f.read().strip()
                    
            # Remove double quotes from the 'description' variable
            description = description.replace('"', '')

            # Check if the description is not empty
            if not description:
                print_color("RED", "\n-> Error: Description cannot be empty. Please try again.\n")

        # Step 1.5.8: Activate the virtual environment to use pre-commit installation
        # Determine the virtual environment activation script path based on the operating system
        if os.name == 'nt':  # Windows
            venv_folder = 'Scripts'
        else:  # Linux
            venv_folder = 'bin'
            
        activate_script = os.path.join('backend', '.venv', venv_folder, 'activate')

        # Activate the virtual environment
        activate_command = f"source {activate_script}" if os.name != 'nt' else activate_script
        subprocess.run(["bash", "-c", activate_command], check=True)

        # Step 1.5.9: Commit and push changes
        if not description:
            subprocess.run(["git", "commit", "-m", message])
        else:
            subprocess.run(["git", "commit", "-m", message, "-m", description])
        subprocess.run(["git", "push", "origin", branch])

        # Step 1.5.10: Deactivate the virtual environment
        subprocess.run(["deactivate"])

        # Step 1.5.11: Navigate to the project directory (to correctly finish the setup.sh script)
        os.chdir("backend/")

        # Step 1.5.12: Inform the user that changes have been committed and pushed
        print_color("RED", "\nChanges have been committed and pushed to the branch '{}'.\n".format(branch))
    elif additional_action == "6":
        print("\nExiting...\n")
        exit(1)
    else:
        print("\nInvalid choice. Exiting...\n")
        exit(1)
elif choice == "2":
    print("\nYou chose Production Deployment Setup.\n")
    # Add additional actions for Production Deployment Setup if needed
elif choice == "3":
    print("\nExiting...\n")
    exit(1)
    # Add additional actions for production mode if needed
else:
    print("\nInvalid choice. Exiting...\n")
    exit(1)
