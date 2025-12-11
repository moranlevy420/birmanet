#!/bin/bash
echo "========================================"
echo "  Pension Funds Explorer - Starting..."
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    echo "Please install Python from https://www.python.org/downloads/"
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo
echo "Starting the app..."
echo "The browser will open automatically."
echo "To stop the app, press Ctrl+C"
echo

# Run Streamlit
streamlit run pensia_app.py

