@echo off
title Workflow Sentinel - Dev Mode (Backend + Frontend)
echo =======================================================
echo    Workflow Sentinel: Starting Backend ^& Frontend (Dev)
echo =======================================================

echo.
echo [*] Launching Python FastAPI Backend on port 8000 in a new window...
start "Workflow Sentinel Backend (FastAPI)" cmd /k "python start.py"

echo [*] Launching Frontend (Vite) on port 5173 in a new window...
start "Workflow Sentinel Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo [OK] Both servers started!
echo      - Backend API: http://localhost:8000
echo      - Frontend Dev: http://localhost:5173
echo.
pause

