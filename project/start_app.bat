@echo off
echo Starting Agentic SQL-RAG...

:: Start Backend
start cmd /k "cd backend && call venv\Scripts\activate && uvicorn app:app --reload --host 0.0.0.0 --port 8000"

:: Start Frontend
start cmd /k "cd frontend && npm run dev"

echo ===================================================
echo Backend running on http://localhost:8000
echo Frontend running on http://localhost:5173
echo ===================================================
echo Ensure Ollama is running with 'ollama run phi3:mini'
pause