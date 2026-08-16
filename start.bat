@echo off
echo ===================================
echo   Starting VESTIGIUM App
echo ===================================

echo Starting Backend server...
start "Vestigium Backend" cmd /k "cd backend && python run.py"

echo Starting Frontend server...
start "Vestigium Frontend" cmd /k "cd frontend && npm run dev"

echo Services are launching in separate windows!
echo Once the Vite server is ready, the app will be available at http://localhost:5173
pause
