@echo off
setlocal enabledelayedexpansion
title OPS to WAV Audio Converter - Setup and Launcher

echo ============================================================
echo         AIREC / OPS to WAV Audio Converter Launcher
echo ============================================================

:: 1. Check if Python is installed and accessible in PATH
python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=python"
    goto :PYTHON_READY
)

py -3 --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=py -3"
    goto :PYTHON_READY
)

:: Check standard Windows default install paths
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :PYTHON_READY
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :PYTHON_READY
)
if exist "%ProgramFiles%\Python312\python.exe" (
    set "PYTHON_EXE=%ProgramFiles%\Python312\python.exe"
    goto :PYTHON_READY
)
if exist "%ProgramFiles%\Python311\python.exe" (
    set "PYTHON_EXE=%ProgramFiles%\Python311\python.exe"
    goto :PYTHON_READY
)

:: 2. Python is NOT installed - Offer to install it automatically
echo.
echo [!] Python was not detected on this computer.
echo.
echo Would you like to automatically download and install Python now?
set /p INSTALL_CHOICE="Enter 'Y' to install automatically (or 'N' to cancel): "
if /i not "%INSTALL_CHOICE%"=="Y" (
    echo.
    echo Please install Python manually from https://www.python.org/downloads/
    echo Remember to check the box "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo.
echo [*] Checking for Windows Package Manager (winget)...
winget --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [*] Installing Python via winget...
    winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
    if %ERRORLEVEL% equ 0 (
        echo [+] Python installed successfully via winget!
        goto :REFRESH_PATH_AND_RETRY
    )
)

:: Fallback: Download official python installer with PowerShell
echo.
echo [*] Downloading Python installer using PowerShell...
set "PY_INSTALLER=%TEMP%\python_installer.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe', '%PY_INSTALLER%')"

if not exist "%PY_INSTALLER%" (
    echo [ERROR] Failed to download Python installer. Please install Python manually from https://www.python.org/
    pause
    exit /b 1
)

echo [*] Installing Python (with 'Add to PATH' and pip enabled)...
"%PY_INSTALLER%" /passive InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_test=0
del "%PY_INSTALLER%" >nul 2>&1

:REFRESH_PATH_AND_RETRY
echo [*] Refreshing environment variables...
:: Read user PATH from registry to get newly installed Python without requiring restart
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%B"
for /f "tokens=2*" %%A in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%B"
set "PATH=%USER_PATH%;%SYS_PATH%;%PATH%"

python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=python"
    goto :PYTHON_READY
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :PYTHON_READY
)

echo.
echo [!] Python installation finished, but the terminal cannot find it yet.
echo     Please close this window and double-click convert.bat again.
pause
exit /b 0

:PYTHON_READY
echo.
echo [+] Python found: 
%PYTHON_EXE% --version

:: 3. Check and auto-install Python packages (pyogg)
echo.
echo [*] Checking required Python dependencies...
%PYTHON_EXE% -c "import pyogg" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [*] 'pyogg' package is missing. Installing automatically via pip...
    %PYTHON_EXE% -m pip install --upgrade pip >nul 2>&1
    %PYTHON_EXE% -m pip install pyogg
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install 'pyogg'. Please check your internet connection.
        pause
        exit /b 1
    )
    echo [+] 'pyogg' installed successfully!
) else (
    echo [+] 'pyogg' is already installed.
)

:: 4. Launch interactive converter menu
echo.
echo [*] Launching converter interface...
%PYTHON_EXE% "%~dp0converter_menu.py"
pause
