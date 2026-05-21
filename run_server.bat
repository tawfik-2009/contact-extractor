@echo off
echo Starting Contact-AI Server...
echo ----------------------------------------
echo To stop the server, press CTRL+C
echo The server is running at http://0.0.0.0:8080/
echo ----------------------------------------
waitress-serve --port=8080 --threads=4 app:app
pause
