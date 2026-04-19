@echo off
REM Drilling Insight Startup Script for Windows
REM Starts frontend on port 8080 and backend on port 8001

echo.
echo ==========================================
echo Drilling Insight - Full Stack Startup
echo ==========================================
echo.
echo Frontend: http://localhost:8080
echo Backend:  http://localhost:8001
echo.

REM Kill any existing processes on these ports
echo Cleaning up old processes...
netstat -ano | findstr ":8080 " | for /F "tokens=5" %%a in ('findstr /R "."') do taskkill /PID %%a /F 2>nul
netstat -ano | findstr ":8001 " | for /F "tokens=5" %%a in ('findstr /R "."') do taskkill /PID %%a /F 2>nul
timeout /t 2 /nobreak

echo.
echo Starting Backend on port 8001...
cd ai_service
start "Backend - Port 8001" python -m uvicorn main:app --host 0.0.0.0 --port 8001

timeout /t 3 /nobreak

echo.
echo Starting Frontend on port 8080...
cd ..
start "Frontend - Port 8080" npm run dev

echo.
echo ==========================================
echo ✅ Application started successfully!
echo ==========================================
echo.
echo Access the application at:
echo   http://localhost:8080
echo.
echo API available at:
echo   http://localhost:8001
echo.
echo Close these windows to stop the services
echo.
pause
