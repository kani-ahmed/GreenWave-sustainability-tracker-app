#!/bin/bash

# Function to create and activate virtual environment
create_and_activate_env() {
    # Create a virtual environment named 'venv'
    python3 -m venv venv

    # Activate the virtual environment
    # For Windows
    if [[ "$OSTYPE" == "msys" ]]; then
        source venv/Scripts/activate
    else
    # For macOS and Linux
        source venv/bin/activate
    fi

    # Install requirements from requirements.txt
    pip install -r requirements.txt
}

echo "Setting up Python virtual environment and installing dependencies..."

# Check if virtual environment directory exists
if [ ! -d "venv" ]; then
    create_and_activate_env
else
    echo "Virtual environment already exists."

    # Activate the existing virtual environment
    if [[ "$OSTYPE" == "msys" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
fi

echo "Setup complete."

