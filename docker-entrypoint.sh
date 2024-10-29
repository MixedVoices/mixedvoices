#!/bin/bash
# docker-entrypoint.sh

# Initialize the database
python start_db.py

# Start the Flask server
python run_server.py