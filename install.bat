@echo off
echo Installing required packages...
pip install -r requirements.txt

if %ERRORLEVEL% equ 0 (
    echo Installation successful. Starting the application...
    python main.py
) else (
    echo Installation failed. Please check your Python environment and try again.
    pause
)
