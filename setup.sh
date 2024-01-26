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
        print_color "1;31" "\n-> You chose Local Development Mode."

        # Step 2: Navigate to the project directory
        cd backend/

        # Step 3: Check if .env file exists before copying
        if [ ! -f ".env" ]; then
            cp .env.example .env
            print_color "0;32" "\nCopied '.env.example' to '.env'.\n"
        else
            print_color "0;33" "\n'.env' file already exists. Skipping copy step.\n"
        fi

        # Step 4: Check if SECRET_KEY is placeholder before generating
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
        echo -e "Setup complete for Local Development Mode.\n"
        
        # Ask the user if they want to perform additional actions
        print_color "1;37" "Do you want to perform any additional actions?\n"
        echo "1 - Start the FastAPI server"
        echo "2 - Run the ARQ worker"
        echo "3 - Run unit tests"
        echo "4 - Exit"

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
