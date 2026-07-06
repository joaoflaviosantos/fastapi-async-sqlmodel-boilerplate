@echo off
REM install_python.bat
REM Installs Python 3.11 via winget (Windows Package Manager) and Poetry.
REM Run this script as Administrator or it will request elevation automatically.

SET PYTHON_VERSION=3.11.9
SET POETRY_VERSION=2.1.4

echo ==^> Checking for winget (Windows Package Manager)...
where winget >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: winget not found.
    echo Please install the App Installer from the Microsoft Store:
    echo   https://apps.microsoft.com/detail/9NBLGGH4NNS1
    exit /b 1
)

echo ==^> Installing Python %PYTHON_VERSION% via winget...
winget install --id Python.Python.3.11 --version %PYTHON_VERSION% --accept-source-agreements --accept-package-agreements --silent
IF %ERRORLEVEL% NEQ 0 (
    echo WARNING: winget returned a non-zero exit code. Python may already be installed.
)

echo ==^> Refreshing PATH for current session...
SET "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"

echo ==^> Verifying Python installation...
python --version
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: python not found in PATH after installation.
    echo You may need to restart your terminal or add Python to PATH manually.
    exit /b 1
)

echo ==^> Installing Poetry %POETRY_VERSION%...
(Invoke-Expression (New-Object System.Net.WebClient).DownloadString('https://install.python-poetry.org')) 2>nul
REM Fallback: use PowerShell to install Poetry
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python - --version %POETRY_VERSION%"

IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Poetry installation failed.
    exit /b 1
)

echo ==^> Adding Poetry to PATH for current session...
SET "PATH=%APPDATA%\Python\Scripts;%PATH%"

echo ==^> Verifying Poetry installation...
poetry --version
IF %ERRORLEVEL% NEQ 0 (
    echo WARNING: poetry not found in PATH for current session.
    echo Open a new terminal and run: poetry --version
    echo If it still fails, add %%APPDATA%%\Python\Scripts to your system PATH manually.
) ELSE (
    echo.
    echo ============================================================
    echo   Setup complete!
    echo   Python and Poetry are installed.
    echo   You can now run: cd backend ^&^& poetry install
    echo ============================================================
)
