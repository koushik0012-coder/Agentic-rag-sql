@echo off
echo ---------------------------------------------------
echo   EMERGENCY CLEANUP - KILLING ZOMBIE PROCESSES
echo ---------------------------------------------------

echo Killing Python (Backend)...
taskkill /F /IM python.exe /T 2>nul

echo Killing Node (Frontend)...
taskkill /F /IM node.exe /T 2>nul

echo Killing Ollama (AI Model)...
taskkill /F /IM ollama.exe /T 2>nul
taskkill /F /IM "ollama app.exe" /T 2>nul

echo.
echo ---------------------------------------------------
echo   ALL PROCESSES TERMINATED.
echo   You can now restart using 'start_app.bat'
echo   or run 'ollama serve' manually.
echo ---------------------------------------------------
pause
