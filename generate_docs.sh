#!/bin/bash

# --- Stori AI Documentation Generator ---

echo "--- Stori AI Documentation Generator ---"

# Navigate to the application directory
echo "Changing to Actividad8/ directory..."
cd Actividad8 || { echo "Error: Could not change to Actividad8 directory. Make sure you are running this script from the project root."; exit 1; }

# Install/update dependencies
echo "Installing dependencies from requirements.txt..."
python3 -m pip install -r requirements.txt --break-system-packages

# Set environment variable to solve protobuf issue (if needed)
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Launch the documentation generation script
echo "Starting the documentation generation process..."
python3 generate_docs.py

echo "Boosting the generated documentation for improved structure and deduplication..."
python3 boost_docs.py

echo "--- Script finished. ---"
echo "Check the Actividad8/ directory for the newly generated HTML files and the updated index.html." 