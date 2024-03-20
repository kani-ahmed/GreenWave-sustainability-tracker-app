#!/bin/bash

# Function to create and activate virtual environment
create_and_activate_env() {
    echo "Creating a virtual environment..."
    # Create a virtual environment named 'venv'
    python3 -m venv venv

    echo "Activating the virtual environment..."
    # Activate the virtual environment for macOS and Linux
    source venv/bin/activate

    echo "Installing dependencies from requirements.txt..."
    # Install requirements from requirements.txt
    pip install -r requirements.txt
}

echo "Setting up Python virtual environment and installing dependencies..."

# Check if virtual environment directory exists
if [ ! -d "venv" ]; then
    create_and_activate_env
else
    echo "Virtual environment already exists. Activating..."
    # Activate the existing virtual environment
    source venv/bin/activate
fi

echo "Setup complete."
