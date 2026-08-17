@echo off
netstat -ano | findstr :5002 | findstr LISTENING >nul
if %errorlevel%==0 exit /b 0
cd /d C:\Users\USER\Desktop\3
python app.py > logs\server.log 2>&1