#!/bin/bash
echo "Starting Contact-AI Server..."
echo "----------------------------------------"
echo "To stop the server, press CTRL+C"
echo "The server is running at http://0.0.0.0:8080/"
echo "----------------------------------------"
gunicorn --workers 4 --bind 0.0.0.0:8080 app:app
