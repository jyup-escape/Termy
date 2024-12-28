@echo off
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python and add it to the PATH environment variable.
    pause
    exit /b
)
echo Upgrading pip...
python -m pip install --upgrade pip
echo Installing required modules...
python -m pip install PyQt5 psutil

if %ERRORLEVEL% EQU 0 (
    echo Modules installed successfully.
) else (
    echo An error occurred during installation.
)
pause
exit
