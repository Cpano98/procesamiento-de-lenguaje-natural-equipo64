#!/bin/bash

# --- Stori RAG Chatbot Runner ---

echo "--- Stori RAG Chatbot ---"

# Navigate to the application directory
echo "Changing to Actividad8/ directory..."
cd Actividad8 || { echo "Error: Could not change to Actividad8 directory. Make sure you are running this script from the project root."; exit 1; }

# Install dependencies
echo "Installing dependencies from requirements.txt..."
python3 -m pip install -r requirements.txt --break-system-packages

# Set environment variable to solve protobuf issue
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Check if port 7862 is in use and kill the process if it is
PORT_PID=$(lsof -t -i:7862)
if [ ! -z "$PORT_PID" ]; then
    echo "Port 7862 is in use. Killing existing process..."
    kill $PORT_PID
    sleep 2
fi

# Launch the application
echo "Launching chatbot application at http://127.0.0.1:7862"
echo "Open Actividad8/index.html in your browser to see the interface."

python3 chatbot_app.py &
APP_PID=$!

# Wait for user to stop the script
echo "Chatbot application is running. Press [Enter] to stop."
read -r

# Stop the application
echo "Stopping chatbot application..."
kill $APP_PID

echo "Script finished."