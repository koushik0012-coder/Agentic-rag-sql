@echo off
echo ==========================================
echo      Agentic SQL-RAG Setup Script
echo ==========================================

echo [1/4] Checking for Python...
python --version
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.9+.
    pause
    exit /b
)

echo [2/4] Checking for Node.js...
node --version
if %errorlevel% neq 0 (
    echo Node.js is not installed. Please install Node.js.
    pause
    exit /b
)

echo [3/4] Installing Backend Dependencies...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install Python dependencies.
    pause
    exit /b
)
cd ..

echo [4/4] Setup Complete! 
echo Please ensure you have Ollama running with 'phi3:mini'.
echo Run 'start_backend.bat' and 'start_frontend.bat' to launch the project.
pause
