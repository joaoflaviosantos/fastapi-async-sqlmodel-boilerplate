#!/bin/bash

# Function to print text in color
print_color() {
    COLOR=$1
    TEXT=$2
    echo -e "\e[${COLOR}m${TEXT}\e[0m"
}

# Function to read user input with color
read_color() {
    COLOR=$1
    PROMPT=$2
    read -p "$(print_color "${COLOR}" "${PROMPT}")" input
    echo "${input}"
}

# Function to display help menu
display_help() {
    print_color "1;37" "Select an option:\n"
    echo "1 - Local Development Mode"
    echo "2 - Production Deployment Setup"
    echo "3 - Exit"
}

# Function to check if a command is available
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python 3.11 and Poetry are installed
if ! command_exists python3.11 || ! command_exists poetry; then
    echo -e "\nError: Python 3.11 and Poetry are required. Please install them before running this setup."
    exit 1
fi

# Print boilerplate name and description
print_color "1;33" "#########################################################################################################################"
print_color "1;33" "####################################### FastAPI Async SQLModel Boilerplate (Setup) ######################################"
print_color "1;33" "#########################################################################################################################\n"

print_color "0;32" "Supercharge your FastAPI development. A backend for perfectionists with deadlines and lovers of asynchronous programming.\n"

# Display help menu initially
display_help

# Ask user for action
choice=$(read_color "1;37" "\nEnter the number corresponding to your choice: ")

# Process user choice
case $choice in
    1)
        print_color "1;31" "\n-> You chose Local Development Mode...\n"

        # Step 2: Navigate to the project directory
        cd backend/

        # Step 3: Install dependencies
        poetry install

        # Step 4: Check if .env file exists before copying
        if [ ! -f ".env" ]; then
            cp .env.example .env
            print_color "0;32" "\nCopied '.env.example' to '.env'.\n"
        else
            print_color "0;33" "\n'.env' file already exists. Skipping copy step.\n"
        fi

        # Step 5: Check if SECRET_KEY is placeholder before generating
        secret_key_placeholder="here-should-be-a-secret-key"
        current_secret_key=$(grep -E '^SECRET_KEY=' .env | awk -F'=' '{print $2}' | tr -d '"')
        if [ "$current_secret_key" == "$secret_key_placeholder" ]; then
            secret_key=$(poetry run python -c "from fastapi import FastAPI; import secrets; print(secrets.token_urlsafe(32))")
            sed -i "s/${secret_key_placeholder}/${secret_key}/" .env
            print_color "0;32" "\nGenerated and set a secure secret key in '.env'.\n"
        else
            print_color "0;33" "'SECRET_KEY' in '.env' is already set. Skipping generation step.\n"
        fi

        # Inform the user to modify other environment variables in ".env"
        print_color "1;34" "Please modify other environment variables in 'backend/.env' as needed.\n"

        # Display a success message for Local Development Mode
        print_color "1;31" "-> Setup complete for Local Development Mode...\n"
        
        # Ask the user if they want to perform additional actions
        print_color "1;37" "Do you want to perform any additional actions?\n"
        echo "1 - Start the FastAPI server"
        echo "2 - Start the ARQ worker"
        echo "3 - Run unit tests"
        echo "4 - Run linting and formatting checks"
        echo "5 - Commit and Push Changes"
        echo "6 - Exit"

        additional_action=$(read_color "1;37" "\nEnter the number corresponding to your choice: ")

        # Process user's additional action choice
        case $additional_action in
            1)
                print_color "1;31" "\n-> Starting the FastAPI server...\n"
                poetry run uvicorn src.main:app --reload
                print_color "1;31" "\n-> Stopping the FastAPI server...\n"
                ;;
            2)
                print_color "1;31" "\n-> Running the ARQ worker...\n"
                poetry run arq src.worker.WorkerSettings
                print_color "1;31" "\n-> Finished running the ARQ worker...\n"
                ;;
            3)
                print_color "1;31" "\n-> Running unit tests...\n"
                poetry run python -m pytest -vv ./tests
                print_color "1;31" "\n-> Finished running unit tests...\n"
                ;;
            4)
                print_color "1;31" "\n-> Running linting and formatting checks...\n"
                poetry run python -m black .
                print_color "1;31" "\n-> Finished running linting and formatting checks...\n"
                ;;
            5)
                print_color "1;31" "\n-> Committing and pushing changes...\n"

                # Return to root directory
                cd ..

                # Add all files
                # TODO: allow the user to define which files or folders should be committed
                git add .

                # Clean the variables at the beginning
                BRANCH=""
                MESSAGE=""
                DESCRIPTION=""

                # Loop until BRANCH is not empty
                while [ -z "$BRANCH" ]; do
                    # Get the branch name from the user
                    BRANCH=$(read_color "1;37" "Please enter the branch name: ")

                    # Check if BRANCH is not empty
                    if [ -z "$BRANCH" ]; then
                        print_color "1;31" "\n-> Error: Branch name cannot be empty. Please try again.\n"
                    fi
                done

                # Loop until MESSAGE is not empty
                while [ -z "$MESSAGE" ]; do
                    # Get the commit message from the user
                    MESSAGE=$(read_color "1;37" "Please enter the commit message: ")

                    # Check if MESSAGE is not empty
                    if [ -z "$MESSAGE" ]; then
                        print_color "1;31" "\n-> Error: Commit message cannot be empty. Please try again.\n"
                    fi
                done

                # Ask the user if they want to include an additional commit description (optional)
                read -p "Do you want to include an additional commit description? (y/n): " include_description

                # Check if the user wants to include an additional description
                if [ "$include_description" = "y" ]; then
                    # Loop until DESCRIPTION is not empty
                    while [ -z "$DESCRIPTION" ]; do
                        # Get the commit description message from the user
                        echo "Please enter the commit description message:"
                        echo "Press Ctrl+D to finish entering the description."

                        # Use 'cat' to capture the user's multiline input
                        DESCRIPTION=$(cat)

                        # Check if DESCRIPTION is not empty
                        if [ -z "$DESCRIPTION" ]; then
                            print_color "1;31" "\n-> Error: Description cannot be empty. Please try again.\n"
                        fi
                    done
                fi

                source backend/.venv/bin/activate

                # Commit and push changes
                if [ -z "$DESCRIPTION" ]; then
                    git commit -m "$MESSAGE"
                else
                    git commit -m "$MESSAGE" -m "$DESCRIPTION"
                fi
                git push origin $BRANCH

                deactivate

                # Navigate to the project directory (to correctly finish the setup.sh script)
                cd backend/

                # Clean the variables at the end
                BRANCH=""
                MESSAGE=""
                DESCRIPTION=""

                # Inform the user that changes have been committed and pushed
                print_color "0;32" "\nChanges have been committed and pushed to the branch '$BRANCH'.\n"
                ;;
            6)
                echo "\nExiting...\n"
                exit 1
                ;;
            *)
                echo -e "\nInvalid choice. Exiting...\n"
                exit 1
                ;;
        esac
        ;;
    2)
        echo -e "\nYou chose Production Deployment Setup.\n"
        # Add additional actions for Production Deployment Setup if needed
        ;;
    3)
        echo -e "\nExiting...\n"
        exit 1
        # Add additional actions for production mode if needed
        ;;
    *)
        echo -e "\nInvalid choice. Exiting...\n"
        exit 1
        ;;
esac

# Last step: Return to the root project directory
cd ..
